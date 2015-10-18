Meteor.publish null, ->
  return unless @userId

  User.documents.find
    _id: @userId
    active: true
  ,
    fields:
      isFacilitator: 1
      iClickerId: 1

Accounts.validateLoginAttempt (loginAttempt) ->
  return false unless loginAttempt.allowed

  # No dot at the end of the error message to match Meteor messages.
  throw new Meteor.Error 403, "User is deactivated" unless loginAttempt.user.active

  return true

# Forbid users from making any modifications to their user document.
User.Meta.collection.deny
  update: ->
    true

MAX_LINE_LENGTH = 68

# Formats text into lines of MAX_LINE_LENGTH width for pretty emails
wrap = (text, maxLength=MAX_LINE_LENGTH) ->
  lines = for line in text.split '\n'
    if line.length <= maxLength
      line
    else
      words = line.split ' '
      if words.length is 1
        line
      else
        ls = [words.shift()]
        for word in words
          if ls[ls.length - 1].length + word.length + 1 <= maxLength
            ls[ls.length - 1] += ' ' + word
          else
            ls.push word
        ls.join '\n'

  lines.join '\n'

indent = (text, amount) ->
  assert amount >= 0
  padding = (' ' for i in [0...amount]).join ''
  lines = for line in text.split '\n'
    padding + line
  lines.join '\n'

wrapWithIndent = (text, indentAmount=2, wrapLength=MAX_LINE_LENGTH) ->
  # Wrap text to narrower width
  text = wrap text, wrapLength - indentAmount

  # Indent it to reach back to full width
  indent text, indentAmount

Accounts.emailTemplates.siteName = Meteor.settings.public.siteName if Meteor.settings?.public?.siteName
Accounts.emailTemplates.from = Meteor.settings.from if Meteor.settings?.from

Accounts.emailTemplates.resetPassword.subject = (user) ->
  """[#{ Accounts.emailTemplates.siteName }] Password reset"""
Accounts.emailTemplates.resetPassword.text = (user, url) ->
  url = url.replace '#/', ''

  # Construct email body
  parts = []

  parts.push """
  Hello #{ user.emails[0].address }!

  This message was sent to you because you requested a password reset for your user account at #{ Accounts.emailTemplates.siteName } with username "#{ user.emails[0].address }". If you have already done so or don't want to, you can safely ignore this email.

  Please click the link below and choose a new password:

  #{ url }

  Please also be careful to open a complete link. Your email client might have broken it into several lines.

  Your username, in case you have forgotten: #{ user.emails[0].address }

  Yours,


  #{ Accounts.emailTemplates.siteName }
  #{ Meteor.absoluteUrl() }
  """

  wrap parts.join ''

Accounts.emailTemplates.enrollAccount.subject = (user) ->
  """[#{ Accounts.emailTemplates.siteName }] An account has been created for you"""
Accounts.emailTemplates.enrollAccount.text = (user, url) ->
  url = url.replace '#/', ''

  # Construct email body
  parts = []

  parts.push """
  Hello #{ user.emails[0].address }!

  Please click the link below to start using your account:

  #{ url }

  If you have already done so or don't want to, you can safely ignore this email.

  Please also be careful to open a complete link. Your email client might have broken it into several lines.

  To learn more about #{ Accounts.emailTemplates.siteName }, visit:

  #{ Meteor.absoluteUrl() }

  Yours,


  #{ Accounts.emailTemplates.siteName }
  #{ Meteor.absoluteUrl() }
  """

  wrap parts.join ''
