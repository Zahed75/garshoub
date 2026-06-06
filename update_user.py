user = env.ref('base.user_admin')
user.write({'login': 'zayanori.business@gmail.com', 'password': 'Z@y@nori2@26#'})
env.cr.commit()
print("UPDATED_SUCCESSFULLY")
