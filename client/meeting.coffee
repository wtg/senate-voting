Template.meeting.agendaItems = ->
  AgendaItem.documents.find
    'meeting._id': @_id
  ,
    sort: [
      ['order', 'asc']
    ]

Template.meeting.rendered = ->
  @autorun =>
    if Meteor.user()?.isFacilitator
      @$('.agenda-items').sortable
        stop: (event, ui) =>
          agendaItem = ui.item.get(0)
          previous = ui.item.prev().get(0)
          next = ui.item.next().get(0)

          if not previous and next # Moving to the top of the list
            newOrder = Blaze.getData(next).order - 1
          else if not next and previous # Moving to the bottom of the list
            newOrder = Blaze.getData(previous).order + 1
          else if next and previous
            newOrder = (Blaze.getData(next).order + Blaze.getData(previous).order) / 2

          if newOrder?
            Meteor.call 'agenda-item-order', Blaze.getData(agendaItem)._id, newOrder, (error) ->
              return alert error if error
    else
      try
        @$('.agenda-items').sortable('destroy')
      catch error
        # Ignore any errors when destroying

Template.addMeeting.events
  'submit form': (event, template) ->
    event.preventDefault()

    name = template.$('.name').val().trim()

    return unless name

    Meteor.call 'create-meeting', name, (error) ->
      return alert error if error

      template.$('.name').val('')

    return # Make sure CoffeeScript does not return anything
