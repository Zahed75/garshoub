user = env.ref('base.user_admin')
user.password = 'test@123'
env.cr.commit()
print(f"PASSWORD_SET_FOR: {user.login}")
