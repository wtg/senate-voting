Template.registerHelper 'currentUserIsFacilitator', (options) ->
  !!Meteor.user()?.isFacilitator

Template.registerHelper 'currentUserId', (options) ->
  Meteor.userId()
