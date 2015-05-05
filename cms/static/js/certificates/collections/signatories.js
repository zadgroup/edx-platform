define([
    'backbone', 'js/certificates/models/signatory'
],
function(Backbone, Signatory) {
    'use strict';
    console.log("signatory_collection.start");
    var SignatoryCollection = Backbone.Collection.extend({
        model: Signatory,
        initialize: function(attr, options) {
            if(options.certificateId) {
                this.url = options.certificateUrl + '/' + options.certificateId + '/signatories';
            }
        }
    });
    console.log("signatory_collection.SignatoryCollection");
    console.log(SignatoryCollection);
    console.log("signatory_collection.return");
    return SignatoryCollection;
});
