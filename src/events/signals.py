from django.dispatch import Signal

# Signal sent when a new donation is posted
# Provides arguments: 'sender', 'donation', 'request'
donation_posted = Signal()

# Signal sent when a donation is successfully claimed by an NGO
# Provides arguments: 'sender', 'donation', 'ngo'
donation_claimed = Signal()

# Signal sent when a donation is confirmed collected
# Provides arguments: 'sender', 'donation', 'ngo'
donation_collected = Signal()

# Signal sent when an NGO has been approved/verified by an admin
# Provides arguments: 'sender', 'ngo_user', 'admin_user'
ngo_verified = Signal()

# Signal sent when a user has been banned by an admin
# Provides arguments: 'sender', 'target_user', 'admin_user'
user_banned = Signal()
