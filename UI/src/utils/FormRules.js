/* jshint esversion: 6 */
/* jshint expr: true */
/* jshint strict:true */
/* jslint node: true */

/* eslint-disable */

import { i18n } from '@/plugins/i18n/i18n';
const locale = i18n.global;

export default {
    required: v => !!v || v === false || locale.t('forms.required'),
    requiredNumber: v => typeof v === 'number' || locale.t('forms.required'),
    requiredList: v => (v && v.length > 0) || locale.t('forms.required'),
    emailLocal: v =>
        (v &&
            /^(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/.test(
                v
            )) ||
            locale.t('forms.email_must_valid'),
    newPasswordRules: function() {
        const requiredError = locale.t('forms.new_password_required');
        const nonCompliantError = locale.t('forms.non_compliant_password');
        const dontMatchError = locale.t('forms.passwords_dont_match');
        return [
            v => !!v || requiredError,
            // () => !this.isSimilarity || this.isSimilarity,
            () =>
            this.errors.length <= 0 || nonCompliantError,
            v =>
            v === this.newPasswordConfirm ||
            this.newPasswordConfirm.length === 0 ||
            dontMatchError,
        ];
    },
    isValidUrl: v => {
        const pattern = new RegExp('^(https?:\\/\\/)?'+ // protocol
            '((([a-z\\d]([a-z\\d-]*[a-z\\d])*)\\.)+[a-z]{2,}|'+ // domain name
            '((\\d{1,3}\\.){3}\\d{1,3}))'+ // OR ip (v4) address
            '(\\:\\d+)?$', 'i'); // port
        return !!pattern.test(v) || locale.t('forms.invalid_url');
    },
};
