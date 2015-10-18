counters = new DirectCollection 'counters'

getNextSequence = (name) ->
  loop
    try

      ret = counters.findAndModify
        _id: name
      ,
        []
      ,
        $inc:
          seq: 1
      ,
        new: true
        upsert: true

      return ret.seq

    # If a duplicate error is thrown we should retry
    catch error
      # TODO: Improve when https://jira.mongodb.org/browse/SERVER-3069
      if /E11000 duplicate key error index:.*counters\.\$_id/.test error.err
        continue
      throw error

Meteor.methods
  'create-agenda-item': (meetingId, actionItem, description) ->
    check meetingId, DocumentId
    check actionItem, Boolean
    check description, NonEmptyString

    throw new Meteor.Error 401, "User not signed in." unless @userId
    throw new Meteor.Error 403, "User is not a facilitator." unless User.documents.findOne(@userId, fields: isFacilitator: 1)?.isFacilitator

    # TODO: Verify that meetingId exists

    AgendaItem.documents.insert
      createdAt: new Date()
      author:
        _id: @userId
      meeting:
        _id: meetingId
      order: getNextSequence 'agendaItem'
      actionItem: actionItem
      description: description
      notes: Random.id() unless actionItem

  'agenda-item-order': (agendaItemId, order) ->
    check agendaItemId, DocumentId
    check order, Number

    throw new Meteor.Error 401, "User not signed in." unless @userId
    throw new Meteor.Error 403, "User is not a facilitator." unless User.documents.findOne(@userId, fields: isFacilitator: 1)?.isFacilitator

    AgendaItem.documents.update
      _id: agendaItemId
    ,
      $set:
        order: order

new PublishEndpoint 'agendaitems-by-meeting-id', (meetingId) ->
  check meetingId, DocumentId

  AgendaItem.documents.find
    'meeting._id': meetingId
