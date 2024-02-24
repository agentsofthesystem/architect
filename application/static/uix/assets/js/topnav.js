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

    function showProductMenu(){
        $('.' + product_menu_class)[0].style = 'display: block;';
        $(main_container_class)[0].style = 'display: none;';
        resetOpacity(product_menu_class);
        fadeElementIn(product_menu_class);
    }

    function  hideProductMenu(){
        $('.' + product_menu_class)[0].style = 'display: none; opacity: 0;';
        $('.main-container')[0].style = '';
        resetOpacity(product_menu_class);
    }

    function showDocMenu(){
        $('.' + docs_menu_class)[0].style = '';
        $('.main-container')[0].style = 'display: none;';
        resetOpacity(docs_menu_class);
        fadeElementIn(docs_menu_class);
    }

    function hideDocMenu(){
        $('.' + docs_menu_class)[0].style = 'display: none;';
        $('.main-container')[0].style = '';
        resetOpacity(docs_menu_class);
    }

    if(product_link != null){

        document.getElementById('product-topnav-item').onmouseover = function() {

            if( !is_on_product_menu_item){
                showProductMenu();
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

            if( !is_on_doc_menu_item){
                showDocMenu();
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
