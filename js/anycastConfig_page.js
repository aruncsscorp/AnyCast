// Copyright 2018 BlueCat Networks. All rights reserved.
// JavaScript for your page goes in here.
$(document).ready(function()
{
    $('#instructions').hide();
    var connectionSetUp = false;
    var updatetextField;
    var updateConfig;
    var clearConfig;
    var getConfig;
    var textArea = $('#update').remove();
    $('#main-container').after(textArea);
   $('#dns_edge_url').prop("disabled",false);
   $('#client_id').prop("disabled",false);
   $('#password').prop("disabled",false);
   $('#ip_address').prop("disabled",false);
    $('#submit').prop('disabled', false);
    $('#port').prop('disabled', false);
    $('#logout').prop('disabled', false);
    $('span#spangif').hide();
    $('#update').hide();
    $(document).on('click', '#logout', function(event) {
        console.log('logging out');
        event.preventDefault();
        $.ajax({
            url: 'logout',
            type: 'POST',
            success: function(data) {
                console.log('responce from logout request', data);
                if (data.redirect) {
                window.location.href = data.redirect;
                }
            }
        })
    });

    $(document).on('click', '#submit', function(event) {
        event.preventDefault();
        $('#instructions').show();
        console.log("Clicked Submit button");
        var myform = document.getElementById("anycastConfig_page_form");
        var fd = new FormData(myform );
        $('#daemon-status').html(` <table class="dataframe" border="1">
      <thead>
        <tr style="text-align: right;">
          <th>Daemon</th>
          <th>Running Status</th>
          <th>Running Configuration Status</th>
          <th>Staged Configuration Status</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td> Zebra </td>
          <td><div class="lds-ellipsis"><div></div><div></div><div></div><div></div></div></td>
          <td><div class="lds-ellipsis"><div></div><div></div><div></div><div></div></div></td>
          <td><div class="lds-ellipsis"><div></div><div></div><div></div><div></div></div></td>
        </tr>
        <tr>
          <td> OSPDF </td>
          <td><div class="lds-ellipsis"><div></div><div></div><div></div><div></div></div></td>
          <td><div class="lds-ellipsis"><div></div><div></div><div></div><div></div></div></td>
          <td><div class="lds-ellipsis"><div></div><div></div><div></div><div></div></div></td>
        </tr>
        <tr>
          <td> BGPD </td>
          <td><div class="lds-ellipsis"><div></div><div></div><div></div><div></div></div></td>
          <td><div class="lds-ellipsis"><div></div><div></div><div></div><div></div></div></td>
          <td><div class="lds-ellipsis"><div></div><div></div><div></div><div></div></div></td>
        </tr>
      </tbody>
    </table>`);
        
        $.ajax({
            url: "form",
            data: fd,
            cache: false,
            processData: false,
            contentType: false,
            type: 'POST',
            success: function (dataofconfirm) {
                console.log('Tis is responce from ajax call :', dataofconfirm);
                if (dataofconfirm.output) {
                    $('#update').show();
                    connectionSetUp = true;
                    setInterval(function() {
                        debugall();
                    }, 15000);
                    ajaxCallFunction('update_status');
                                    }
                    else if (dataofconfirm.exception) {
                        $('#daemon-status').html(' ');               
                        alert(dataofconfirm.exception);
                        if (dataofconfirm.redirect) {
                            window.location.href = dataofconfirm.redirect;
                            }
                    }
            }
        });
    });

function ajaxCallFunction(flask_url) {
    console.log('looping');
    //var selectedOption = $('#daemon-status-select').val();
    if (connectionSetUp === true) {
        console.log(connectionSetUp);
        $.ajax({
            url: flask_url,
            type: 'POST',
            //data: {option: selectedOption},
            success: function(data) {
                console.log(data);
                $('#daemon-status').html(data.output);
                $('#daemon-status-select').remove();
                $('#daemon-status').after(data.select_field);
                //textFieldUpdateAjaxCall('update_textfield');

            }        
        });
    }
}
});

function getconfigfile(event, option) {
    event.preventDefault();
    textFieldUpdateAjaxCall('update_textfield', option);
}

function textFieldUpdateAjaxCall(flask_url, selectedOption) {
    console.log('textFieldUpdateAjaxCall');
    console.log('selected option :', selectedOption);
    $('#option').html(selectedOption);
        $.ajax({
            url: flask_url,
            type: 'POST',
            data: {option: selectedOption},
            success: function(data) {
                console.log(data);
                $('textarea').val(data.text_field);
            }        
        });
    }
    
function cleartextarea(event, selectedOption) {
    event.preventDefault();
    $('#option').html(selectedOption);
    $('textarea').val("This is not configured \n update required configuration")
} 

function clearrunConfiguration(event) {
    event.preventDefault();
    $('#update #clear-run span').show();
    var option = $('#option').text();
    console.log('clearrunConfiguration');
        $.ajax({
            url: 'clear_run_configuration',
            type: 'POST',
            data: {option: option},
            success: function(data) {
                console.log(data);
                $('#update #clear-run span').hide();
                $('#daemon-status').html(data.output);
                $('#daemon-status-select').remove();
                $('#daemon-status').after(data.select_field);
                $('#update input').each(function() {
                    console.log(this);
                    if (this.value === option){
                        this.trigger('click');
                    }
                })
            }        
        });
}

function updateConfiguration(event) {
    event.preventDefault();
    $('#update #update span').show();
    var option = $('#option').text();
    console.log('updateConfiguration daemon ', option)
    var confText = $('#configured-daemon').val();
    console.log('this is text from field', confText);
        $.ajax({
            url: 'update_configuration',
            type: 'POST',
            data: {option: option,
                    confText : confText},
            success: function(data) {
                $('#update #update span').hide();
                if (data.exception){
                    alert(data.exception);
                }
                else {
                console.log(data);
                $('#daemon-status').html(data.output);
                $('#daemon-status-select').remove();
                $('#daemon-status').after(data.select_field);
                $('#update input').each(function() {
                    console.log(this.val());
                    if (this.value === option){
                        this.trigger('click');
                        console.log('click was triggered')
                    }
                })
            } }       
        });
}

function clearthesetConfiguration(event) {
    event.preventDefault();
    $('#update #clear span').show();
    var option = $('#option').text();
    console.log('clearthesetConfiguration');
        $.ajax({
            url: 'clear_configuration',
            type: 'POST',
            data: {option: option},
            success: function(data) {
                console.log(data);
                $('#update #clear span').hide();
                $('#daemon-status').html(data.output);
                $('#daemon-status-select').remove();
                $('#daemon-status').after(data.select_field);
                $('#update input').each(function() {
                    console.log(this);
                    if (this.value === option){
                        this.trigger('click');
                    }
                })
            }        
        });
}

function applythestagedConfiguration(event) {
    event.preventDefault();
    $('#update #apply span').show();
    var option = $('#option').text();
    var confText = $('#configured-daemon').val();
    console.log('applythestagedConfiguration');
    $.ajax({
        url : 'apply_configuration',
        type : 'POST',
        data : {option : option,
                confText : confText},
        success : function(data) {
            $('#update #apply span').hide();
            if (data.exception) {
                alert(data.exception)
            }
            else { 
            console.log(data);
            $('#daemon-status').html(data.output);
            $('#daemon-status-select').remove();
            $('#daemon-status').after(data.select_field);
        }}
    })
}

function debugall() {
    console.log('debugall');
    $.ajax({
        url: 'debug',
        type : 'POST',
        success : function(data) {
            console.log(data);
            $('#Debug').html(data.debug_output);
        }
    });
}

function stoporstartDaemon(daemon, status,el) {
    console.log(daemon, status);
    if (status ==='\u00D7') {

        if (confirm('Do you want to start '+daemon)) {
            console.log(el.textContent);
            local_el = el.textContent;
            var local_looper = setInterval(function() {
                console.log(el);
                
                if (local_el === '&#215;') {
                    el.innerHTML = '&#10003;';
                    local_el = '&#10003;';
                    }
                else {
                    el.innerHTML = '&#215;';
                    local_el = '&#215;';
                    }
            }, 500); 
        }
        $.ajax({
            url: 'run_daemon',
            type: 'POST',
            data: {option : daemon},
            success: function(data) {
                console.log('responce form run daemon');
                clearInterval(local_looper);
            if (data.exception) {
                alert(data.exception)
            }
            else { 
            console.log(data);
            $('#daemon-status').html(data.output);
            $('#daemon-status-select').remove();
            $('#daemon-status').after(data.select_field);
            }},
            error: function() {
                clearInterval(local_looper);
            }
        });
        
    }
    else {
        if (confirm('Do you want to stop '+ daemon)) {
            
            console.log(el.textContent);
            local_el = el.textContent;
            var local_looper = setInterval(function() {
                console.log(el);
                if (local_el === '&#215;') {
                    el.innerHTML ='&#10003;';
                    local_el = '&#10003;';
                    }
                else {
                    el.innerHTML = '&#215;';
                    local_el = '&#215;';
                    }
           }, 500);
        } 
        $.ajax({
             url: 'stop_daemon',
             type: 'POST',
             data: {option : daemon},
             success: function(data) {
                 console.log('responce form stop daemon');
                 clearInterval(local_looper);
            if (data.exception) {
                alert(data.exception)
            }
            else { 
            console.log(data);
            $('#daemon-status').html(data.output);
            $('#daemon-status-select').remove();
            $('#daemon-status').after(data.select_field);
             }},
             error: function() {
                 clearInterval(local_looper);
             }
         });
    }
}

function showrunConf(daemon){
   console.log(daemon);
   textFieldUpdateAjaxCall('update_textfield', daemon);
}

function showstagedConf(daemon) {
    $('#option').html(daemon);

    console.log(daemon);
       $.ajax({
       url: 'update_textfield_staged',
       type : 'POST',
       data : {option : daemon},
       success : function(data) {
           console.log(data);
            $('textarea').val(data.text_field);

       },
       error: function(data) {
           console.log(data);
       }
   }); 

}