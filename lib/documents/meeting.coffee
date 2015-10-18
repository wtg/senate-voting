SLUG_MAX_LENGTH = 80

class @Meeting extends Document
  # createdAt: time of creation
  # facilitator:
  #   _id: User id
  # name: text
  # slug: slug from the meeting name

  @Meta
    name: 'Meeting'
    fields: =>
      facilitator: @ReferenceField User
      slug: @GeneratedField 'self', ['name'], (fields) ->
        if fields.name
          [fields._id, URLify2 fields.name, SLUG_MAX_LENGTH]
        else
          [fields._id, '']
