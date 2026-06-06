user = env.ref('base.user_admin')
print(f"PASSWORD_HASH: {user.password}")
