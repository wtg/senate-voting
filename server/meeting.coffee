Meteor.methods
  'create-meeting': (name) ->
    check name, NonEmptyString

    throw new Meteor.Error 401, "User not signed in." unless @userId
    throw new Meteor.Error 403, "User is not a facilitator." unless User.documents.findOne(@userId, fields: isFacilitator: 1)?.isFacilitator

    Meeting.documents.insert
      createdAt: new Date()
      facilitator:
        _id: @userId
      name: name

new PublishEndpoint 'meeting-by-id', (meetingId) ->
  check meetingId, DocumentId

  Meeting.documents.find
    _id: meetingId

new PublishEndpoint 'meetings', ->
  Meeting.documents.find {},
    fields:
      items: 0
