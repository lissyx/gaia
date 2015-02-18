/* globals BaseModule */

'use strict';

(function(exports) {
  var CameraTrigger = function() {};

  BaseModule.create(CameraTrigger, {
    name: 'CameraTrigger',
    DEBUG: true,
    TRACE: false,

    _start: function nsm_start() {
      window.addEventListener('holdcamera', this.triggerCamera.bind(this));
    },

    triggerCamera: function(event) {
      this.debug('Received holdcamera');
      var activity = new MozActivity({
        name: 'record',
        data: {
          type: 'photos'
        }
      });
    }

  });
}());
