
$("#id_have_suit").change(function() {
			if ($(this).val() == "হ্যাঁ") {
				$('#x').show();
				$('#id_suit_type').attr('required','');
				$('#id_suit_type').attr('data-error', 'This field is required.');
        $('#id_suit_number').attr('required','');
				$('#id_suit_number').attr('data-error', 'This field is required.');
			} else {
				$('#x').hide();
				$('#id_suit_type').removeAttr('required');
				$('#id_suit_type').removeAttr('data-error');
        $('#id_suit_number').removeAttr('required');
				$('#id_suit_number').removeAttr('data-error');
			}
		});
	$("#id_have_suit").trigger("change");// JavaScript Document
