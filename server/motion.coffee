Meteor.methods
  'create-motion': (meetingId, agendaItemId, motion) ->
    check meetingId, DocumentId
    check agendaItemId, DocumentId
    check motion, NonEmptyString

    throw new Meteor.Error 401, "User not signed in." unless @userId

    # TODO: Verify that meetingId and agendaItemId exist and that agendaItemId is really an agendaItemId of meetingId

    # TODO: Set all other fields as well
    Motion.documents.insert
      createdAt: new Date()
      author:
        _id: @userId
      meeting:
        _id: meetingId
      agendaItem:
        _id: agendaItemId
      motion: motion
      pros: Random.id()
      cons: Random.id()
      notes: Random.id()
      yes: []
      no: []
      abstain: []
      veto: []

new PublishEndpoint 'motions-by-meeting-id', (meetingId) ->
  check meetingId, DocumentId

  Motion.documents.find
    'meeting._id': meetingId
