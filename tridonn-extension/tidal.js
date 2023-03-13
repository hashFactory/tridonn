
// re-enable browser console
if (!("console" in window) || !("firebug" in console))
{
  console.log = null;
  console.log;         // null

  delete console.log;

  // Original by Xaerxess
  var i = document.createElement('iframe');
  i.style.display = 'none';
  document.body.appendChild(i);
  window.console = i.contentWindow.console;
}

var tracks = [];// = document.querySelectorAll('[data-type="mediaItem"]');

var rating_divs = [];
var ratings = {};

var target_hue = 30;

//var body = document.querySelector('body');

function reqListener() {
  var req = this;

  if (req.readyState === req.DONE) {
        if (req.status === 200) {
          console.log(req.responseText);
          console.log(req.responseURL);
          var rating = (parseFloat(req.responseText)) * 60;
          var requested_split = req.responseURL.split("/");
          var requested_track = requested_split[requested_split.length-2];
          console.log("response from " + requested_track);

          var new_sat = ((rating-5) / 12.0) * 50.0;
          var new_lig = ((rating-3) / 12.0) * 40.0;
          var new_bright = (240-((15-rating) * 8));

          console.log(ratings[requested_track]);
          if (document.getElementById(requested_track) != null) {
            var elem = document.getElementById(requested_track);
            elem.innerHTML = rating.toString().match(/\d+\.\d{2}/)[0];
            elem.parentNode.parentNode.setAttribute('style', " background-color: hsl(340, " + (new_sat).toString() + "%, " + (new_lig).toString() + "%; ");

            //elem.style = elem.style + " border: 1px solid hsl(0, 50%, 50%); ";
            elem.setAttribute('style', elem.getAttribute('style') + " border: 2px solid hsl(340, " + (new_sat*2).toString() + "%, " + (new_lig*2).toString() + "%); " + " background-color: hsl(340, " + (new_sat).toString() + "%, " + (new_lig).toString() + "%); font-weight: " + (parseInt(new_sat*18)).toString() + "; color: rgb(" + (new_bright).toString() + ", " + (new_bright).toString() + ", " + (new_bright).toString() + ");");
            //elem.style = elem.style + " background-color: hsl(0, " + (new_sat).toString() + "%, " + (new_lig).toString() + "%); ";

          }
        }
  }
}

function setup_track(s) {
    var value = s.attributes.getNamedItem("data-track--content-id");

    if (value) {
        value = value.nodeValue;
    }

    //const newstyle = "align-items: center; contain: strict; display: flex; height: 100%; justify-content: center; left: 0; position: absolute; top: 0; width: 100px;";
    console.log("Checking " + value);

    if (document.getElementById(value) != undefined) {
      //if (ratings[value].innerHTML != "...") {
        console.log("Wanted to load " + value.toString() + " but existing div found.");
        return;
      //}
    }

    var rating_display = document.createElement("div");
    ratings[value] = rating_display;
    ratings[value].id = value;
    ratings[value].innerHTML = "...";

    const newstyle = "display: flex; min-width: 3.2em; padding-right: 0px; justify-content: center; align-items: center; margin-right: 6px; ";
    ratings[value].style = newstyle;
    //rating_display.style = newstyle;

    var req = new XMLHttpRequest();
    req.addEventListener("load", reqListener);
    req.open('GET', 'http://rate.trido.fr/track/' + value + "/", true);
    //req.setRequestHeader("X-Requested-With", "XMLHttpRequest");
    //req.setRequestHeader("Origin", "listen.tidal.com");
    req.responseType = 'text';

    s.children[0].insertAdjacentElement('afterbegin', ratings[value]);
    // request track here

    console.log(value.toString());
    req.send(null);

    //console.log(req.responseText);
};


//body.addEventListener("keydown", (event) => {
//if (event.keyCode === 219) {
function runAgain() {
  setTimeout(() => {
    console.log("Searching for tracks!.");

    tracks = document.querySelectorAll('[data-type="mediaItem"]');
    tracks.forEach(setup_track);
    runAgain();
  }, 2000);
}

runAgain();

    //console.log("Copied value!");
    //console.log(text);
//}
// --------------------------
//});

