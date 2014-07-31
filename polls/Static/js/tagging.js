$(document).ready(function() {

	//scroll is captured, just how should it be recorded?
	$(window).scroll(function() {
		//do something
		console.log("Scrolled!");
	});

	var callback = function(data) {
	    $.ajax({
	        url: '/vote/',
	        type: 'post',
	        data: { "id": data.id, "up": data.upvoted, "down": data.downvoted}
	    });
	};
	
	$('.upvote').upvote({id: $(this).data("id"), callback: callback});

})

$( "#add-new-entry" ).click(function() {
  var inputText = $("#new-text-entry").val();
  var entryNum = $("#entry-number").val();
  console.log(inputText);
  // Passing the jQuery Response
  var jqxhr = $.post( "/addNewEntryFunc/" , {
		'input_text' : inputText,
		'entry_number' : entryNum
	},function (response) {
	  	console.log(response);
	  	if (response.success === true) {
	  		alert( "You have successfully added a new entry" );
	  		//Enabled = false
	  	} else {
	  		alert("error");
	  	}
	  })
});

function swapToDec(){
	document.getElementById("increment").id = "decrement";
}

function swapToInc(){
	document.getElementById("decrement").id = "increment";
}


$( ".increment" ).click(function() {
  var tid = $(this).val();
  console.log(tid);
  // Passing the jQuery Response
  var jqxhr = $.post( "/increment/" , {
  		'tid' : tid
	},function (response) {
	  	console.log(response);
	  	if (response.success === true) {
	  		alert( "You have successfully incremented tag" );
	  		window.location.reload();
	  	} else {
	  		alert("error");
	  	}
	})
});


$( ".decrement" ).click(function() {
	var tid = $(this).val();
	console.log(tid);
	//passing jQuery response
	var jqxhr = $.post( "/decrement/" , {
		'tid' : tid
	}, function(response) {
		console.log(response);
		if (response.success == true){
			alert( "You have successfully decremented tag" );
			window.location.reload();
		} else {
			alert("error");
		}
	})
});