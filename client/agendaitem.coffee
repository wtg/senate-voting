Template.actionItem.helpers
  motions: ->
    Motion.documents.find
      'agendaItem._id': @_id
    ,
      sort: [
        # The oldest motion first
        ['createdAt', 'asc']
      ]

Template.addAgendaItem.events
  'submit form': (event, template) ->
    event.preventDefault()

    actionItem = template.$('.action-item').is(':checked')
    description = template.$('.description').val().trim()

    return unless description

    Meteor.call 'create-agenda-item', @_id, actionItem, description, (error) ->
      return alert error if error

      template.$('.action-item').attr('checked', false)
      template.$('.description').val('')

    return # Make sure CoffeeScript does not return anything
