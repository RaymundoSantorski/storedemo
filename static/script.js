var stripe = Stripe('pk_test_51HU3xZEIyvFHfGwOL8UDyTstXcodlWZ3aApx1WnbNbHdl3c1YZI5UzhltDJozjQjVor1NRA1uM0Q2TRLQMyfzOQT00zKsIIyAW');

var checkoutButton = document.getElementById('checkout-button');

function checkout() {
	// Create a new Checkout Session using the server-side endpoint you
        // created in step 3.
        fetch('/create-checkout-session', {
          method: 'POST',
        })
        .then(function(response) {
          return response.json();
        })
        .then(function(session) {
          return stripe.redirectToCheckout({ sessionId: session.id });
        })
        .then(function(result) {
          // If `redirectToCheckout` fails due to a browser or network
          // error, you should display the localized error message to your
          // customer using `error.message`.
          if (result.error) {
            alert(result.error.message);
          }
        })
        .catch(function(error) {
          console.error('Error:', error);
        });
      };

function payNow(id){
  var url = "payNow/"+id
  fetch(url, {
    method: 'POST',
  })
  .then(function(response) {
    return response.json();
  })
  .then(function(session) {
    return stripe.redirectToCheckout({ sessionId: session.id });
  })
  .then(function(result) {
    // If `redirectToCheckout` fails due to a browser or network
    // error, you should display the localized error message to your
    // customer using `error.message`.
    if (result.error) {
      alert(result.error.message);
    }
  })
  .catch(function(error) {
    console.error('Error:', error);
  });
};