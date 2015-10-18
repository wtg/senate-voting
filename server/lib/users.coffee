fs = Npm.require 'fs'

watchUsersFile = (usersFile) ->
  watcher = fs.watch usersFile, {persistent: false}, Meteor.bindEnvironment (event, filename) ->
    watcher.close()
    syncUsers usersFile

# Using debounce so that if there is a series of changes, only the last one
# does something. This is also useful to have a slight delay between the last
# change and reading the file, because some editors are replacing the file
# on every save instead of modifying the content directly and if are too quick
# new file might not yet be in place.
syncUsers = _.debounce Meteor.bindEnvironment (usersFile) ->
  try
    users = JSON.parse fs.readFileSync usersFile
    usersEmail = _.pluck users, 'email'

    User.documents.find(
      'emails.address':
        $nin: usersEmail
      active:
        $ne: false
    ).forEach (user) ->
      count = User.documents.update
        _id: user._id
        'emails.address':
          $nin: usersEmail
        active:
          $ne: false
      ,
        $set:
          active: false

      if count
        console.log "user account has been disabled", user.emails[0].address
        # TODO: Send an e-mail that user account has been disabled
        null

    for user in users
      count = User.documents.update
        'emails.address': user.email
        active:
          $ne: true
      ,
        $set:
          active: true

      if count
        console.log "user account has been enabled", user.email
        # TODO: Send an e-mail that user account has been enabled
        null

      count = User.documents.update
        'emails.address': user.email
        isFacilitator:
          $ne: !!user.isFacilitator
      ,
        $set:
          isFacilitator: !!user.isFacilitator

      if count
        if !!user.isFacilitator
          console.log "user account has become a facilitator", user.email
          # TODO: Send an e-mail that user account has become a facilitator
          null
        else
          console.log "user account has ceased to be a facilitator", user.email
          # TODO: Send an e-mail that user account has ceased to be a facilitator
          null

      unless User.documents.exists('emails.address': user.email)
        userId = Accounts.createUser
          email: user.email

        User.documents.update userId,
          $set:
            active: true
            isFacilitator: !!user.isFacilitator

        Accounts.sendEnrollmentEmail userId
  catch error
    Log.error "Error syncing users: #{ error }"

  watchUsersFile usersFile
,
  10 # ms

Meteor.startup ->
  usersFile = Meteor.settings?.usersFile

  unless usersFile
    Log.warn "No users file specified in settings"
    return

  syncUsers usersFile
