
/* ------------------------------
 Loading イメージ表示関数
 引数： msg 画面に表示する文言
 ------------------------------ */
function dispLoading(msg){
  // 引数なし（メッセージなし）を許容
  if( msg == undefined ){
    msg = "";
  }
  // 画面表示メッセージ
  var dispMsg = "<div class='loadingMsg'>" + msg + "</div>";
  // ローディング画像が表示されていない場合のみ出力
  if($("#loading").length == 0){
    $("body").append("<div id='loading'>" + dispMsg + "</div>");
  }
}
 
/* ------------------------------
 Loading イメージ削除関数
 ------------------------------ */
function removeLoading(){
  $("#loading").remove();
}

/* ------------------------------
 非同期処理の組み込みイメージ
 ------------------------------ */
 $(function () {
  $("#proc_button").click( function() {
 
    // 処理前に Loading 画像を表示
    dispLoading("処理中...");
 
    // 非同期処理
    $.ajax({
      //url : "http://127.0.0.1:5000/stockcheck",
      url : "/stockcheck",
      type:"GET",
      dataType:"json"
    })
    // 通信成功時
    .done( function(data) {
      showMsg("成功しました");
    })
    // 通信失敗時
    .fail( function(data) {
      showMsg("失敗しました");
    })
    // 処理終了時
    .always( function(data) {
      // Lading 画像を消す
      removeLoading();
    });
  });
});