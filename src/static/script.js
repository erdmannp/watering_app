$( document ).ready(function() {
  function updateSensors() {
    $.getJSON('/get_sensor_values/', function(response){
      $("#sensor1_humidity").text(response.sensor1);
      $("#sensor2_humidity").text(response.sensor2);
      $("#sensor3_humidity").text(response.sensor3);
      $("#sensor4_humidity").text(response.sensor4);
      $("#sensor5_humidity").text(response.sensor5);
      $("#sensor6_humidity").text(response.sensor6);
      $("#datetime").text(response.datetime);
      
    });    
  }

  updateSensors();  
  setInterval(updateSensors, 1000 * 10);
});


document.addEventListener('DOMContentLoaded', (event) => {
    var dragSrcEl = null;
    
 

      



    function handleDragStart(e) {
      this.style.opacity = '0.4';
      
      dragSrcEl = this;
  
      e.dataTransfer.effectAllowed = 'move';
      e.dataTransfer.setData('text/html', this.innerHTML);
    }
  
    function handleDragOver(e) {
      if (e.preventDefault) {
        e.preventDefault();
      }
  
      e.dataTransfer.dropEffect = 'move';
      
      return false;
    }
  
    function handleDragEnter(e) {
      this.classList.add('over');
    }
  
    function handleDragLeave(e) {
      this.classList.remove('over');
    }
  
    function handleDrop(e) {
      if (e.stopPropagation) {
        e.stopPropagation(); // stops the browser from redirecting.
      }
      
      if (dragSrcEl != this) {
        dragSrcEl.innerHTML = this.innerHTML;
        this.innerHTML = e.dataTransfer.getData('text/html');
      }
      
      return false;
    }
  
    function handleDragEnd(e) {
      this.style.opacity = '1';
      
      items.forEach(function (item) {
        item.classList.remove('over');
      });
    }
    
    
    let items = document.querySelectorAll('.container');
    items.forEach(function(item) {
      item.addEventListener('dragstart', handleDragStart, false);
      item.addEventListener('dragenter', handleDragEnter, false);
      item.addEventListener('dragover', handleDragOver, false);
      item.addEventListener('dragleave', handleDragLeave, false);
      item.addEventListener('drop', handleDrop, false);
      item.addEventListener('dragend', handleDragEnd, false);
    });
  });
  
