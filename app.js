// set variables for environment
var express = require('express');
var app = express();
var path = require('path');

// views as directory for all template files
app.set('views', path.join(__dirname, 'views'));
app.set('view engine', 'ejs'); // use either jade or ejs  

// index page
app.get('/', function(req, res) {
  res.render('view\index');
});
     
// instruct express to server up static assets
app.use(express.static('public'));

// Set server port
app.listen(8080);
console.log('8080 is the magic port for use. Reverse proxying for the win');