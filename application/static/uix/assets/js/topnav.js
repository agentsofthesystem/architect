
$(document).ready(function($){

    product_link = document.getElementById('product-topnav-item');
    docs_link = document.getElementById('docs-topnav-item');

    if(product_link != null){

        document.getElementById('product-topnav-item').onmouseover = function() {
            // do something like for example change the class of a div to change its color :
            $('.product-topnav-child-menu')[0].style = '';
            $('.main-container')[0].style = 'display: none;';
        };
        
        document.getElementById('product-topnav-item').onmouseout = function() {
            // do something like for example change the class of a div to change its color :
            $('.product-topnav-child-menu')[0].style = 'display: none;';
            $('.main-container')[0].style = '';
        };
    }

    if(docs_link != null){
        document.getElementById('docs-topnav-item').onmouseover = function() {
            // do something like for example change the class of a div to change its color :
            $('.docs-topnav-child-menu')[0].style = '';
            $('.main-container')[0].style = 'display: none;';
        };
        
        document.getElementById('docs-topnav-item').onmouseout = function() {
            // do something like for example change the class of a div to change its color :
            $('.docs-topnav-child-menu')[0].style = 'display: none;';
            $('.main-container')[0].style = '';
        };
    }

});
