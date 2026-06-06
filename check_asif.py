user = env.ref('base.user_admin')
print(f"LOGIN: {user.login}")
print(f"PASSWORD_HASH: {user.password}")
