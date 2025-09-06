$(function() {
  $("#sidebar-toggle").on("click", function() {
    $(".sidebar").toggleClass("active");
    $("#overlay").toggleClass("show");
  });

  $("#overlay").on("click", function() {
    $(".sidebar").removeClass("active");
    $(this).removeClass("show");
  });
});