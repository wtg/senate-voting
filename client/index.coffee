Template.index.helpers
  meetings: ->
    Meeting.documents.find {},
      sort: [
        # The newest meeting first
        ['createdAt', 'desc']
      ]
