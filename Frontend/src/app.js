import * as angular from "angular";

angular.module('poorify', [require('@uirouter/angularjs').default, require('angular-ui-grid')])
    .run(
        function ($rootScope, $state) {
            $rootScope.$state = $state;
        })
    .constant('BACKEND_URL', 'http://localhost:5000/');
