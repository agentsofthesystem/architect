function resetOpacity(menu_class) {
    var element = document.getElementsByClassName(menu_class)[0];

    if( 'opacity' in element.style){
        element.style.setProperty('opacity', '0')
    }
    else{
        element.style.opacity = 0;
    }
}

function fadeElementIn(menu_class) {
    var timeout = 100;
    var element = document.getElementsByClassName(menu_class)[0];
    var current_opacity = element.style.opacity;
    var new_opacity = parseFloat(current_opacity);

    if(current_opacity < 1) {
       new_opacity += .075;
       setTimeout(function(){fadeElementIn(menu_class)}, timeout);
    }

    element.style.opacity = new_opacity;
}

$(document).ready(function($){

    product_link = document.getElementById('product-topnav-item');
    docs_link = document.getElementById('docs-topnav-item');

    main_container_class = '.main-container'
    product_menu_class = 'product-topnav-child-menu'
    docs_menu_class = 'docs-topnav-child-menu'

    is_on_product_menu_item = false;
    is_on_doc_menu_item = false;
    is_product_menu_open = false;
    is_doc_menu_open = false;

    function showProductMenu(){

        // Hide both for good measure
        if(is_doc_menu_open){
            hideDocMenu();
            hideProductMenu();
        }

        $('.' + product_menu_class)[0].style = 'display: block;';
        $(main_container_class)[0].style = 'display: none;';
        resetOpacity(product_menu_class);
        fadeElementIn(product_menu_class);
        is_product_menu_open = true;
        //console.log("Showing Product Menu")
    }

    function hideProductMenu(){
        $('.' + product_menu_class)[0].style = 'display: none; opacity: 0;';
        $('.main-container')[0].style = '';
        resetOpacity(product_menu_class);
        is_product_menu_open = false;
        //console.log("Hiding Product Menu")
    }

    function showDocMenu(){

        // Hide both for good measure
        if(is_product_menu_open){
            hideDocMenu();
            hideProductMenu();
        }

        $('.' + docs_menu_class)[0].style = '';
        $('.main-container')[0].style = 'display: none;';
        resetOpacity(docs_menu_class);
        fadeElementIn(docs_menu_class);
        is_doc_menu_open = true;
        //console.log("Showing Doc Menu")
    }

    function hideDocMenu(){
        $('.' + docs_menu_class)[0].style = 'display: none;';
        $('.main-container')[0].style = '';
        resetOpacity(docs_menu_class);
        is_doc_menu_open = false;
        //console.log("Hiding Doc Menu")
    }

    if(product_link != null){

        document.getElementById('product-topnav-item').onmouseover = function() {

            // Toggle on/off
            if( !is_on_product_menu_item){
                setTimeout(function(){showProductMenu()}, 400);
            }
            else{
                hideProductMenu();
                is_on_product_menu_item = false;
                return
            }

            is_on_product_menu_item = !is_on_product_menu_item;
        };
    }

    if(docs_link != null){
        document.getElementById('docs-topnav-item').onmouseover = function() {

            // Toggle on/off
            if( !is_on_doc_menu_item){
                setTimeout(function(){showDocMenu()}, 400);
            }
            else{
                hideDocMenu();
                is_on_doc_menu_item = false;
                return
            }

            is_on_doc_menu_item = !is_on_doc_menu_item;
        };

    }

});
