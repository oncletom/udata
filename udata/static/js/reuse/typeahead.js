/**
 * Typeahead.js/Bloodhound completion definition for reuses
 */
define([
    'jquery',
    'bloodhound',
    'hbs!templates/search/header',
    'hbs!templates/search/suggestion',
    'i18n',
    'logger'
], function($, Bloodhound, header, suggestion, i18n, log) {
    var MAX = 3,
        engine = new Bloodhound({
            name: 'reuses',
            limit: MAX,
            queryTokenizer: Bloodhound.tokenizers.whitespace,
            datumTokenizer: function(d) {
                return Bloodhound.tokenizers.whitespace(d.name);
            },
            remote: {
                url: '/api/suggest/reuses?q=%QUERY&size='+MAX,
                // Keep until model is uniformised
                filter: function(response) {
                    return $.map(response, function(row, idx) {
                        row.name = row.title;
                        return row;
                    })
                }
            }
        });

    engine.initialize();

    return {
        name: 'reuses',
        source: engine.ttAdapter(),
        displayKey: 'name',
        limit: MAX,
        templates: {
            header: header({title: i18n._('Reuses')}),
            suggestion: suggestion
        }
    };
});
