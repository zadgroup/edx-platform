define([
    'backbone', 'js/certificates/models/signatory'
],
function(Backbone, Signatory) {
    'use strict';
    console.log("signatory_collection.start");
    var SignatoryCollection = Backbone.Collection.extend({
        model: Signatory,
        url: '/certificates/edX/DemoX/Demo_Course/signatories'

    });
    console.log("signatory_collection.SignatoryCollection");
    console.log(SignatoryCollection);
    console.log("signatory_collection.return")
    return SignatoryCollection;
});
