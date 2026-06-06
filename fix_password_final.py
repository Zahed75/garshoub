user = env['res.users'].search([('login', '=', '16i23y58gr@ozsaip.com')], limit=1)
if user:
    user.write({'password': 'test@123'})
    env.cr.commit()
    print(f"SUCCESS_PASSWORD_SET_FOR_{user.login}")
else:
    print("USER_NOT_FOUND")
