# From Meteor's random/random.js
@UNMISTAKABLE_CHARS = '23456789ABCDEFGHJKLMNPQRSTWXYZabcdefghijkmnopqrstuvwxyz'
INVALID_ID_CHARS_REGEX = new RegExp "[^#{ UNMISTAKABLE_CHARS }]"

@NonEmptyString = Match.Where (x) ->
  check x, String
  x.trim().length > 0

@DocumentId = Match.Where (x) ->
  check x, String
  check x, Match.Where (y) -> y.length is 17
  not INVALID_ID_CHARS_REGEX.test x
