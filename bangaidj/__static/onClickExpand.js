
$("#id_present_objection_status").change(function() {
			if ($(this).val() == "নিষ্পন্ন") {
				$('#otherFieldGroupDiv').show();
				$('#id_finished_date').attr('required','');
				$('#id_finished_date').attr('data-error', 'This field is required.');
        $('#id_finished_letter_no').attr('required','');
				$('#id_finished_letter_no').attr('data-error', 'This field is required.');
			} else {
				$('#otherFieldGroupDiv').hide();
				$('#id_finished_date').removeAttr('required');
				$('#id_finished_date').removeAttr('data-error');
        $('#id_finished_letter_no').removeAttr('required');
				$('#id_finished_letter_no').removeAttr('data-error');
			}
		});
	$("#id_present_objection_status").trigger("change");// JavaScript Document


	$("#id_present_objection_status").change(function() {
				if ($(this).val() == "অনিষ্পন্ন") {
					$('#AnotherFieldGroupDiv').show();
					$('#id_issued_letter_date').attr('required','');
					$('#id_issued_letter_date').attr('data-error', 'This field is required.');
	        $('#id_issued_letter_no').attr('required','');
					$('#id_issued_letter_no').attr('data-error', 'This field is required.');
				} else {
					$('#AnotherFieldGroupDiv').hide();
					$('#id_issued_letter_date').removeAttr('required');
					$('#id_issued_letter_date').removeAttr('data-error');
	        $('#id_issued_letter_no').removeAttr('required');
					$('#id_issued_letter_no').removeAttr('data-error');
				}
			});
		$("#id_present_objection_status").trigger("change");// JavaScript Document
