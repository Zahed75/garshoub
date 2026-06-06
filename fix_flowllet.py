user = env.ref('base.user_admin')
user.write({'login': 'besgieuq6o@yzcalo.com', 'password': 'test@123'})
env.cr.commit()
print("FLOWLLET_FIXED")
