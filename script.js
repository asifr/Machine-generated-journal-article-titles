var currentItem = {};
var right = 0;
var total = 0;
var debug = 0;

function getItem () {
	jQuery.ajax({
		url: "faker.php",
		dataType: "json",
		success: function(results){
			currentItem = results;
			$("#item").html(results.title);
			if (debug == 1) {
				console.log(results);
			};
			// update score
			updateScore();
		}
	});
}

function updateScore () {
	$("#correct").html(right);
	$("#total").html(total);
}

function saveScore (choice) {
	jQuery.ajax({
		url: "save.php",
		dataType: "json",
		data:{'id': currentItem.id, 'actual': currentItem.real, 'choice': choice}
	});
}

function init() {
	getItem();
	$("#real").click(function(){
		if (currentItem.real == 'real') {
			$("#item").addClass('right').html('Right!');
			setTimeout(function() {
				$("#item").removeClass('right');
				right=right+1;
				getItem();
			}, 1200);
		};
		if (currentItem.real == 'fake') {
			$("#item").addClass('wrong').html('Wrong!');
			setTimeout(function() {
				$("#item").removeClass('wrong');
				getItem();
			}, 1200);
		};
		total=total+1;
		saveScore('real');
	});
	$("#fake").click(function(){
		if (currentItem.real == 'fake') {
			$("#item").addClass('right').html('Right!');
			setTimeout(function() {
				$("#item").removeClass('right');
				right=right+1;
				getItem();
			}, 1200);
		};
		if (currentItem.real == 'real') {
			$("#item").addClass('wrong').html('Wrong!');
			setTimeout(function() {
				$("#item").removeClass('wrong');
				getItem();
			}, 1200);
		};
		total=total+1;
		saveScore('fake');
	});
}

jQuery(document).ready(function($){
	init();
});
