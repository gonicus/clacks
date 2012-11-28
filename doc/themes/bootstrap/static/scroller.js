var lineIndex = -1;
var paused = false;
var tick = 10;
var typeSpeed0 = 75 / tick;
var linePause0 = 200 / tick;
var typeSpeed = typeSpeed0;
var linePause = linePause0;

var currentLine = '';

function startDisplay(tt) {
  paused = true;
  displayNextLine(1, tt);
}

stopStart = function() {
  paused = ! paused;
  //$('span#pause:first').set('innerHTML', paused ? 'Click to continue' : 'Click to pause');
  $('span#pause:first').html(paused ? 'Click to continue' : 'Click to pause');
}

complete = function() {
  typeSpeed = 0;
  linePause = 0;  
}

function asynch(f) {
  var self = function() {
    var args = Array.prototype.slice.call(arguments); 
    var wait = args[0];
    if (wait > 0) {
      if (! paused) {args[0] = wait - 1;}
      setTimeout(function() {self.apply(null, args);}, tick);
      } else {
      args = args.slice(1);
      f.apply(null, args);
    }
  }
  return self;
}

function nextLine() {
  var i = lineIndex + 1;
  if (i >= text.length) {i = 0;}
  return text[i];
}

function isComment(text) {return text.match('^#');}
function isCode(text) {return text.match('^(>|\\.){3}');}

function isCommand(text) {return text.match('^[A-Z]+$');}
function isOutput(text) {
  return !(isCode(text) || isComment(text) || isCommand(text));
}

displayNextLine = asynch(function(tt) {
  lineIndex++;
  if (lineIndex >= text.length) {
    stopStart();
    lineIndex = 0;
    typeSpeed = typeSpeed0;
    linePause = linePause0;
  }
  currentLine = text[lineIndex];
  if (isComment(currentLine)) {
    displayComment(1, tt, currentLine);
  } else if (isCode(currentLine)) {
    displayCode(1, tt, currentLine);
  } else if (isCommand(currentLine)) {
    command(1, tt, currentLine);
  } else {
    displayOutput(1, tt, currentLine);
  }
});

command = asynch(function(tt) {
  switch(currentLine) {
    case 'CLEAR':
      tt.set('innerHTML', '');
      break;
    case 'PAUSE':
      stopStart();
      break;
  }
  displayNextLine(1, tt);
});

displayComment = asynch(function(tt, text) {
  tt.append('<span class="comment"></span>');
  charByChar(1, tt, text, typeSpeed, linePause, true);
});

displayCode = asynch(function(tt, text) {
  tt.append(text.substring(0, 3));
  tt.append('<span class="code"></span>');
  charByChar(1, tt, text.substring(3), typeSpeed, linePause, true);
});

displayOutput = asynch(function(tt, text) {
  tt.append('<span class="output"></span>');
  charByChar(1, tt, text, 0, isOutput(nextLine()) ? 0 : linePause, true);
});

charByChar = asynch(function(tt, text, speed, pause, nl) {
  if (text.length > 0) {
    var c = text.charAt(0);
    if (c == ' ') {
      tt.children().last().append("&nbsp;");
      if (nl) {
        tt.scrollTop(tt[0].scrollHeight);
      }
      charByChar(0, tt, text.substring(1), speed, pause, false);
    } else {
      tt.children().last().append(text.charAt(0));
      if (nl) {
        tt.scrollTop(tt[0].scrollHeight);
      }
      var s = 0      
      if (typeSpeed) {s = speed / 2 + Math.random() * speed / 2;}
        charByChar(s, tt, text.substring(1), speed, pause, false);
      }
    } else {
      tt.append('<br>');
      displayNextLine(pause, tt);
    }
  });


function loadAndRun(text) {
  $("document").ready(function(){
    startDisplay($('div#tt:first'));
  })
}

