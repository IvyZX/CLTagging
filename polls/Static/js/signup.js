$(document).ready(function() {
	//fill with synchronous functions later

})

$( "#signup-submit" ).click(function() {
  var username = $("#username").val();
  var email = $("#email").val();
  var password = $("#password").val();
  var expert = $("#expert").val();
  var nominal = $("#nominal").val();

  // Passing the jQuery Response
  var jqxhr = $.post( "/adduser/" , {
		'username' : username,
		'user_email' : email,
		'password' : password,
		'is_expert': expert,
		'is_nominal': nominal
	},function (response) {
	  	if (response.success === false) {
	  		alert("Error! Could not signup.");
	  	} else {
	  		console.log(response.redirect)
	  		window.location = response.redirect;
	  	}
	  })
});
