import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class LetterOfCredit(models.Model):
    _name = 'letter.of.credit'
    _description = 'Letter of Credit — Bangladesh Trade Finance'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name desc'

    # ── Core Identification ───────────────────────────────────────────────────
    name = fields.Char(
        string='LC Reference',
        required=True,
        tracking=True,
        default=lambda self: _('New'),
        help='e.g. LC-2024-001',
    )
    lc_type = fields.Selection(
        [('import', 'Import LC'), ('export', 'Export LC')],
        string='LC Type',
        required=True,
        default='import',
        tracking=True,
    )
    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('applied', 'Applied'),
            ('opened', 'Opened'),
            ('docs_received', 'Documents Received'),
            ('retired', 'Retired'),
            ('closed', 'Closed'),
        ],
        string='Status',
        default='draft',
        tracking=True,
        copy=False,
    )

    # ── Financial Fields ──────────────────────────────────────────────────────
    lc_amount = fields.Monetary(
        string='LC Amount',
        currency_field='currency_id',
        required=True,
        tracking=True,
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        required=True,
        default=lambda self: self.env.ref('base.USD', raise_if_not_found=False),
    )
    margin_percentage = fields.Float(
        string='Margin % (Bangladesh Bank)',
        default=25.0,
        help='Bangladesh Bank mandated margin percentage on LC amount.',
    )
    margin_amount = fields.Monetary(
        string='Margin Amount',
        currency_field='currency_id',
        compute='_compute_margin_amount',
        store=True,
    )
    margin_account_id = fields.Many2one(
        'account.account',
        string='LC Margin Asset Account',
        help='Asset account to debit when margin is blocked.',
    )

    # ── Parties ───────────────────────────────────────────────────────────────
    ad_bank_id = fields.Many2one(
        'res.partner',
        string='Authorized Dealer (AD) Bank',
        domain="[('is_ad_bank', '=', True)]",
        tracking=True,
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
    )

    # ── Related Documents ─────────────────────────────────────────────────────
    purchase_order_ids = fields.Many2many(
        'purchase.order',
        'lc_purchase_rel',
        'lc_id',
        'po_id',
        string='Purchase Orders',
        domain="[('state', 'in', ['purchase', 'done'])]",
    )
    sale_order_ids = fields.Many2many(
        'sale.order',
        'lc_sale_rel',
        'lc_id',
        'so_id',
        string='Sale Orders',
        domain="[('state', 'in', ['sale', 'done'])]",
    )
    account_move_ids = fields.One2many(
        'account.move',
        'letter_of_credit_id',
        string='Journal Entries',
    )
    landed_cost_id = fields.Many2one(
        'stock.landed.cost',
        string='Landed Cost',
        help='Linked landed cost record for import duty distribution.',
    )

    # ── Bangladesh Compliance Forms ───────────────────────────────────────────
    lca_form_number = fields.Char(
        string='LCA Form Number',
        tracking=True,
        help='LCA Form reference — required for Import LC opening.',
    )
    exp_form_number = fields.Char(
        string='EXP Form Number',
        tracking=True,
        help='EXP Form number — GATES outbound delivery for Export LCs.',
    )
    imp_form_number = fields.Char(
        string='IMP Form Number',
        tracking=True,
    )

    # ── Registration Certificates ─────────────────────────────────────────────
    irc_number = fields.Char(string='IRC Number', help='Import Registration Certificate')
    irc_expiry = fields.Date(
        string='IRC Expiry Date',
        tracking=True,
        help='Cron will warn 30 days before expiry.',
    )
    erc_number = fields.Char(string='ERC Number', help='Export Registration Certificate')
    erc_expiry = fields.Date(
        string='ERC Expiry Date',
        tracking=True,
        help='Cron will warn 30 days before expiry.',
    )

    # ── Shipping Documents ────────────────────────────────────────────────────
    bill_of_lading = fields.Binary(string='Bill of Lading')
    bill_of_lading_filename = fields.Char()

    notes = fields.Text(string='Internal Remarks')

    # ── Sequence ──────────────────────────────────────────────────────────────
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('letter.of.credit') or _('New')
        return super().create(vals_list)

    # ── Computed ──────────────────────────────────────────────────────────────
    @api.depends('lc_amount', 'margin_percentage')
    def _compute_margin_amount(self):
        for rec in self:
            rec.margin_amount = rec.lc_amount * (rec.margin_percentage / 100.0)

    # ════════════════════════════════════════════════════════════════════════
    # STATE MACHINE — TRANSITION METHODS
    # ════════════════════════════════════════════════════════════════════════

    def action_submit_application(self):
        """Draft → Applied: Submit LCA/EXP form."""
        for rec in self:
            if rec.lc_type == 'import' and not rec.lca_form_number:
                raise UserError(_(
                    'LCA Form Number is required before submitting an Import LC application.'
                ))
            if rec.lc_type == 'export' and not rec.exp_form_number:
                raise UserError(_(
                    'EXP Form Number is required before submitting an Export LC application.'
                ))
            rec.state = 'applied'
            rec.message_post(body=_('📋 LC application submitted for bank review.'))

    def action_open_lc(self):
        """Applied → Opened: AD Bank approves; post margin journal entry."""
        for rec in self:
            if rec.state != 'applied':
                raise UserError(_('LC must be in Applied state to open.'))
            if rec.lc_type == 'import' and not rec.lca_form_number:
                raise UserError(_('LCA Form number is required before opening Import LC.'))
            if not rec.margin_account_id:
                raise UserError(_('Please set the LC Margin Asset Account before opening.'))
            if rec.lc_amount <= 0:
                raise UserError(_('LC Amount must be greater than zero.'))

            # Post margin deduction journal entry
            move = rec._create_margin_journal_entry()
            rec.write({
                'state': 'opened',
                'account_move_ids': [(4, move.id)],
            })
            rec.message_post(
                body=_('🏦 LC Opened. Margin of %s %s blocked. Journal Entry: %s') % (
                    rec.margin_amount, rec.currency_id.name, move.name,
                )
            )

    def action_mark_docs_received(self):
        """Opened → Documents Received."""
        for rec in self:
            if rec.state != 'opened':
                raise UserError(_('LC must be Opened to mark documents as received.'))
            rec.state = 'docs_received'
            rec.message_post(body=_('📦 Shipping documents received by AD Bank.'))

    def action_retire_lc(self):
        """Documents Received → Retired: Post settlement, reverse margin."""
        for rec in self:
            if rec.state != 'docs_received':
                raise UserError(_('Documents must be received before LC retirement.'))
            move = rec._create_retirement_journal_entry()
            rec.write({
                'state': 'retired',
                'account_move_ids': [(4, move.id)],
            })
            rec.message_post(
                body=_('✅ LC Retired. Settlement posted. Journal: %s') % move.name
            )

    def action_close_lc(self):
        """Retired → Closed: All obligations settled."""
        for rec in self:
            if rec.state != 'retired':
                raise UserError(_('LC must be Retired before closing.'))
            rec.state = 'closed'
            rec.message_post(body=_('🔒 LC Closed. All obligations cleared.'))

    # ════════════════════════════════════════════════════════════════════════
    # FINANCIAL ENGINE — JOURNAL ENTRIES
    # ════════════════════════════════════════════════════════════════════════

    def _create_margin_journal_entry(self):
        """
        LC Opened — Margin Deduction
        Dr  LC Margin Asset Account   (margin_amount)
        Cr  Operating Bank Account    (margin_amount)
        """
        self.ensure_one()
        company = self.company_id or self.env.company
        margin_amt = self.margin_amount

        # Get bank account (default company bank account)
        bank_account = self._get_bank_account()

        move_vals = {
            'move_type': 'entry',
            'ref': _('LC Margin Blocked: %s') % self.name,
            'letter_of_credit_id': self.id,
            'journal_id': self._get_misc_journal().id,
            'currency_id': self.currency_id.id,
            'line_ids': [
                (0, 0, {
                    'name': _('LC Margin — %s') % self.name,
                    'account_id': self.margin_account_id.id,
                    'debit': margin_amt,
                    'credit': 0.0,
                    'currency_id': self.currency_id.id,
                }),
                (0, 0, {
                    'name': _('LC Margin Deduction — %s') % self.name,
                    'account_id': bank_account.id,
                    'debit': 0.0,
                    'credit': margin_amt,
                    'currency_id': self.currency_id.id,
                }),
            ],
        }
        move = self.env['account.move'].create(move_vals)
        move.action_post()
        return move

    def _create_retirement_journal_entry(self):
        """
        LC Retirement — Settle AP, reverse margin
        Dr  Accounts Payable
        Cr  LC Margin Asset Account  (partial — margin portion)
        Cr  Operating Bank Account   (balance)
        """
        self.ensure_one()
        margin_amt = self.margin_amount
        balance = self.lc_amount - margin_amt
        bank_account = self._get_bank_account()

        # Get AP account
        ap_account = self.env['account.account'].search([
            ('account_type', '=', 'liability_payable'),
            ('company_id', '=', self.company_id.id),
        ], limit=1)

        if not ap_account:
            raise UserError(_('No Accounts Payable account found. Please configure your Chart of Accounts.'))

        move_vals = {
            'move_type': 'entry',
            'ref': _('LC Retirement: %s') % self.name,
            'letter_of_credit_id': self.id,
            'journal_id': self._get_misc_journal().id,
            'currency_id': self.currency_id.id,
            'line_ids': [
                (0, 0, {
                    'name': _('LC Retirement AP Settlement — %s') % self.name,
                    'account_id': ap_account.id,
                    'debit': self.lc_amount,
                    'credit': 0.0,
                }),
                (0, 0, {
                    'name': _('Margin Released — %s') % self.name,
                    'account_id': self.margin_account_id.id,
                    'debit': 0.0,
                    'credit': margin_amt,
                }),
                (0, 0, {
                    'name': _('Balance Payment — %s') % self.name,
                    'account_id': bank_account.id,
                    'debit': 0.0,
                    'credit': balance,
                }),
            ],
        }
        move = self.env['account.move'].create(move_vals)
        move.action_post()
        return move

    def _get_misc_journal(self):
        journal = self.env['account.journal'].search([
            ('type', '=', 'general'),
            ('company_id', '=', self.company_id.id),
        ], limit=1)
        if not journal:
            raise UserError(_('No Miscellaneous journal found. Please configure journals.'))
        return journal

    def _get_bank_account(self):
        account = self.env['account.account'].search([
            ('account_type', 'in', ['asset_cash', 'asset_current']),
            ('company_id', '=', self.company_id.id),
            ('name', 'ilike', 'bank'),
        ], limit=1)
        if not account:
            # Fallback: any cash/bank account
            account = self.env['account.account'].search([
                ('account_type', 'in', ['asset_cash']),
                ('company_id', '=', self.company_id.id),
            ], limit=1)
        if not account:
            raise UserError(_('No Bank account found. Please configure your Chart of Accounts.'))
        return account

    # ════════════════════════════════════════════════════════════════════════
    # CRON — IRC / ERC EXPIRY WARNINGS
    # ════════════════════════════════════════════════════════════════════════

    @api.model
    def cron_check_certificate_expiry(self):
        """Daily cron: warn 30 days before IRC/ERC expiry."""
        from datetime import date, timedelta
        warning_date = date.today() + timedelta(days=30)

        # IRC expiry
        irc_expiring = self.search([
            ('irc_expiry', '<=', str(warning_date)),
            ('irc_expiry', '>=', str(date.today())),
            ('state', 'not in', ['closed', 'retired']),
        ])
        for lc in irc_expiring:
            lc.activity_schedule(
                'mail.mail_activity_data_warning',
                date_deadline=lc.irc_expiry,
                summary=_('⚠️ IRC Certificate Expiring Soon'),
                note=_('IRC %s expires on %s. Please renew urgently.') % (
                    lc.irc_number, lc.irc_expiry,
                ),
            )

        # ERC expiry
        erc_expiring = self.search([
            ('erc_expiry', '<=', str(warning_date)),
            ('erc_expiry', '>=', str(date.today())),
            ('state', 'not in', ['closed', 'retired']),
        ])
        for lc in erc_expiring:
            lc.activity_schedule(
                'mail.mail_activity_data_warning',
                date_deadline=lc.erc_expiry,
                summary=_('⚠️ ERC Certificate Expiring Soon'),
                note=_('ERC %s expires on %s. Please renew urgently.') % (
                    lc.erc_number, lc.erc_expiry,
                ),
            )

        _logger.info(
            'LC expiry check done: %d IRC, %d ERC warnings created.',
            len(irc_expiring), len(erc_expiring)
        )


class AccountMove(models.Model):
    """Extend account.move to link back to the LC."""
    _inherit = 'account.move'

    letter_of_credit_id = fields.Many2one(
        'letter.of.credit',
        string='Letter of Credit',
        index=True,
    )
