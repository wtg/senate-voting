# Should contain only one document at all times,
# with one field "line" of length at most 16.
displayCollection = new Meteor.Collection null

CLICKER_ID_REGEX = new RegExp '[0-9A-Z]{8}'
# F means retract
RESPONSE_REGEX = new RegExp '[ABCDEF]'

Meteor.methods
  'iclicker-vote': (clickerId, response, time) ->
    check clickerId, Match.Where (x) ->
      CLICKER_ID_REGEX.test x
    check response, Match.Where (x) ->
      RESPONSE_REGEX.test x
    check time, Number

    # TODO: Authenticate

    console.log clickerId, response, time

    displayCollection.upsert {},
      $set:
        line: "#{ clickerId }"

Meteor.publish 'display', ->
  handle = displayCollection.find().observeChanges
    added: (id, fields) =>
      @added 'display', id, fields

    changed: (id, fields) =>
      @changed 'display', id, fields

    removed: (id) =>
      @removed 'display', id

  @ready()

  @onStop =>
    handle.stop()
