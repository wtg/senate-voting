Router.route '/',
  name: 'index'
  template: 'index'
  waitOn: ->
    Meteor.subscribe 'meetings',
      onError: (error) -> alert error

Router.route '/meeting/:_id/:slug?',
  name: 'meeting'
  template: 'meeting'
  waitOn: ->
    [
      Meteor.subscribe 'meeting-by-id', @params._id,
        onError: (error) -> alert error
      Meteor.subscribe 'agendaitems-by-meeting-id', @params._id,
        onError: (error) -> alert error
      Meteor.subscribe 'motions-by-meeting-id', @params._id,
        onError: (error) -> alert error
    ]
  data: ->
    Meeting.documents.findOne @params._id
  onBeforeAction: ->
    meeting = @data()

    return @next() unless meeting

    # @params.slug is undefined if slug is not present in location, so we normalize
    # both meeting.slug and @params.slug to prevent any infinite looping.
    return @next() if (meeting.slug or null) is (@params.slug or null)

    @redirect 'meeting', meeting, replaceState: true

Router.route '/reset-password/:resetPasswordToken',
  action: ->
    # Make sure nobody is logged in, it would be confusing otherwise.
    # TODO: How to make it sure we do not log in in the first place? How could we set autoLoginEnabled in time? Because this logs out user in all tabs
    Meteor.logout()

    Accounts._loginButtonsSession.set 'resetPasswordToken', @params.resetPasswordToken

    # Replacing current page with the index page, without keeping tokens location in the history.
    @redirect 'index', {}, replaceState: true

Router.route '/enroll-account/:enrollAccountToken',
  action: ->
    # Make sure nobody is logged in, it would be confusing otherwise
    # TODO: How to make it sure we do not log in in the first place? How could we set autoLoginEnabled in time? Because this logs out user in all tabs
    Meteor.logout()

    Accounts._loginButtonsSession.set 'enrollAccountToken', @params.enrollAccountToken

    # Replacing current page with the index page, without keeping tokens location in the history.
    @redirect 'index', {}, replaceState: true
