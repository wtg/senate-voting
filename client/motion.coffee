Template.addMotion.events
  'submit form': (event, template) ->
    event.preventDefault()

    motion = template.$('.motion').val().trim()

    return unless motion

    Meteor.call 'create-motion', @meeting._id, @_id, motion, (error) ->
      return alert error if error

      template.$('.motion').val('')

    return # Make sure CoffeeScript does not return anything
