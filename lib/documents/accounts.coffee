class @User extends Document
  # createdAt: time of creation
  # emails: list of
  #   address: e-mail address
  #   verified: is e-mail address verified
  # services: list of authentication/linked services
  # active: is account active or disabled
  # isFacilitator
  # iClickerId

  @Meta
    name: 'User'
    collection: Meteor.users
