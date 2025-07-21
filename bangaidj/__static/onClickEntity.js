
$("#id_isEntity").change(function() {
			if ($(this).val() == "হ্যাঁ") {
				$('#entity').show();
				$('#id_branch_amount').attr('required','');
				$('#id_branch_amount').attr('data-error', 'This field is required.');

			} else {
				$('#entity').hide();
				$('#id_branch_amount').removeAttr('required');
				$('#id_branch_amount').removeAttr('data-error');

			}
		});
	$("#id_isEntity").trigger("change");// JavaScript Document
