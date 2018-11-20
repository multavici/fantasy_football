let form_442 = ["Goal Keeper",
            "Right Back", "Center Back 1", "Center Back 2", "Left back",
            "Right Midfielder", "Central Midfielder 1", "Central Midfielder 2", "Left Midfielder",
            "Center Forward 1", "Center Forward 2",
            "Sub Goal Keeper", "Sub Defender", "Sub Midfielder", "Sub Forward"];
let breaks_442 = [0,4,8,10,14];
let form_433 = ["Goal Keeper",
            "Right Back", "Center Back 1", "Center Back 2", "Left back",
            "Central Midfielder 1", "Central Midfielder 2", "Central Midfielder 3",
            "Right Forward", "Center Forward", "Left Forward",
            "Sub Goal Keeper", "Sub Defender", "Sub Midfielder", "Sub Forward"];
let breaks_433 = [0,4,7,10,14];
let form_352 = ["Goal Keeper",
            "Right Center Back", "Center Back", "Left Center Back",
            "Right Wing Back", "Central Midfielder 1", "Central Midfielder 2", "Central Midfielder 3", "Left Wing Back",
            "Center Forward 1", "Center Forward 2",
            "Sub Goal Keeper", "Sub Defender", "Sub Midfielder", "Sub Forward"];
let breaks_352 = [0,3,8,10,14];

$(document).ready(function(){
    // get the labels for the player positions
    var labels = document.getElementsByTagName('LABEL');
    for (var i = 0; i < labels.length; i++) {
        if (labels[i].htmlFor != '') {
             var elem = document.getElementById(labels[i].htmlFor);
             if (elem)
                elem.label = labels[i];
        }
    }


    // By default show the 433 positions
    for (i = 0; i < 15; i++) {
        console.log('players-'+i)
        console.log(document.getElementById('players-'+i))
        document.getElementById('players-'+i).label.innerHTML = form_433[i];
    }

    // When the radio buttons get clicked, change the names for the positions
    $('input[value="433"]').click(function(){
        for (i = 0; i < 15; i++) {
            document.getElementById('players-'+i).label.innerHTML = form_433[i];
        }
    });
    $('input[value="442"]').click(function(){
        for (i = 0; i < 15; i++) {
            document.getElementById('players-'+i).label.innerHTML = form_442[i];
        }
    });
    $('input[value="352"]').click(function(){
        for (i = 0; i < 15; i++) {
            document.getElementById('players-'+i).label.innerHTML = form_352[i];
        }
    });



});