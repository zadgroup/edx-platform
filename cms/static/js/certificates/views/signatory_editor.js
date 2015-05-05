/**
 * This class defines an editing view for course certificates.
 * It is expected to be backed by a Certificate model.
 */
define(['js/views/utils/view_utils', "js/views/feedback_prompt", "js/views/feedback_notification", 'js/utils/templates', 'underscore', 'jquery', 'gettext'],
function(ViewUtils, PromptView, NotificationView, TemplateUtils, _, $, gettext) {
    'use strict';
    console.log('certificate_editor.start');
    var SignatoryEditorView = Backbone.View.extend({
        tagName: 'div',
        events: {
            'change .signatory-name-input': 'setSignatoryName',
            'change .signatory-title-input': 'setSignatoryTitle',
            'click  .signatory-panel-delete': 'deleteItem'
        },

        className: function () {
            console.log('signatory_editor.className');
            var index = this.getModelIndex(this.model);

            return [
                'signatory-edit',
                'signatory-edit-view-' + index
            ].join(' ');
        },

        initialize: function(options) {
             _.bindAll(this, 'render');
            this.model.bind('change', this.render);
            this.eventAgg = options.eventAgg;
            this.isEditingAllCollections = options.isEditingAllCollections;
            this.template = this.loadTemplate('signatory-editor');
        },

        getTotalSignatoriesOnServer: function() {
            var count = 0;
            this.model.collection.each(function( modelSignatory) {
                if(!modelSignatory.isNew()) {
                    count ++;
                }
            });
            return count;
        },

        getModelIndex: function(givenModel) {
            // return the model index / position in its collection.
            return this.model.collection.indexOf(givenModel);
        },

        loadTemplate: function(name) {
            return TemplateUtils.loadTemplate(name);
        },

        render: function() {
            var attributes = $.extend({}, this.model.attributes, {
                signatory_number: this.getModelIndex(this.model) + 1,
                signatories_count: this.model.collection.length,
                isNew: this.model.isNew(),
                is_editing_all_collections: this.isEditingAllCollections,
                total_saved_signatories: this.getTotalSignatoriesOnServer()
            });

            return $(this.el).html(this.template(attributes));
        },

        setSignatoryName: function(event) {
            if (event && event.preventDefault) { event.preventDefault(); }
            this.model.set(
                'name',
                this.$('.signatory-name-input').val(),
                { silent: true }
            );
        },

        setSignatoryTitle: function(event) {
            if (event && event.preventDefault) { event.preventDefault(); }
            this.model.set(
                'title',
                this.$('.signatory-title-input').val(),
                { silent: true }
            );
        },


        deleteItem: function(event) {
            if (event && event.preventDefault) { event.preventDefault(); }
            var certificate = this.model.get('certificate');
            var model = this.model,
                self = this,
                signatory_number = this.getModelIndex(this.model) + 1;

            ViewUtils.confirmThenRunOperation(
                interpolate(
                    gettext('Delete this signatory %(signatory_number)s?'),
                    {signatory_number: signatory_number}, true
                ),
                interpolate(
                    gettext('Deleting this signatory %(signatory_number)s is permanent and cannot be undone.'),
                    {signatory_number: signatory_number},
                    true
                ),
                gettext('Delete'),
                function() {
                    return ViewUtils.runOperationShowingMessage(
                        gettext('Deleting'),
                        function () {
                            return model.destroy({
                                wait: true,
                                success: function(model, response, options) {
                                    // we are re-rendering the certificate editor view to refresh the UI.
                                    // Event in certificate_editor file.
                                    self.eventAgg.trigger("onSignatoryRemoved", model);
                                },
                                error: function(model, xhr, options){
                                    console.log(model);
                                }
                            });
                        }
                    );
                }
            );
        }
    });

    console.log('certificate_editor.CertificateEditorView');
    console.log(SignatoryEditorView);
    console.log('certificate_editor.return');
    return SignatoryEditorView;
});
