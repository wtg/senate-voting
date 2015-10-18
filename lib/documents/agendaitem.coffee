# TODO: We should also add agenda item time length and then have a clock for it
class @AgendaItem extends Document
  # createdAt: time of creation
  # author:
  #   _id: User id
  # meeting:
  #   _id: Meeting id
  # order: order among all agenda items for this meeting
  # actionItem: boolean
  # description: text
  # notes: textId for notes for discussion item

  @Meta
    name: 'AgendaItem'
    fields: =>
      author: @ReferenceField User
      meeting: @ReferenceField Meeting
