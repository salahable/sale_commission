# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2011 Pexego (<www.pexego.es>). All Rights Reserved
#    $Omar Castiñeira Saavedra$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

"""wizard that add the functionally of blocked a production lot and prodlots affected"""

from osv import osv, fields
from tools.translate import _

class block_production_lot(osv.osv_memory):

    _name = "block.production.lot"

    _columns = {
        'prodlot_id': fields.many2one('stock.production.lot', 'Production lot', required=True, readonly=True),
        'case_name': fields.char('Blockade reason', size=64, required=True),
        'case_description': fields.text('Description', required=True),
        'firmness_grade': fields.selection([('pessimistic', 'Pessimistic'), ('optimistic', 'Optimistic')], 'Firmness', required=True, help="Pessimistic block upstream and downstream, optimistic only upstream")
    }

    _defaults = {
        'firmness_grade': 'pessimistic'
    }

    def default_get(self, cr, uid, fields, context=None):
        """ To get default values for the object.
         @param self: The object pointer.
         @param cr: A database cursor
         @param uid: ID of the user currently logged in
         @param fields: List of fields for which we want default values
         @param context: A standard dictionary
         @return: A dictionary which of fields with values.
        """
        if context is None: context = {}
        prodlot_id = context and context.get('active_id', False) or False
        res = super(block_production_lot, self).default_get(cr, uid, fields, context=context)

        if 'prodlot_id' in fields:
            res.update({'prodlot_id': prodlot_id})

        return res

    def lock_production_lot(self, cr, uid, ids, context=None):
        """set in_alert a production lot and the affected lots"""
        if context is None: context = {}
        #gets the objects
        production_lot_obj = self.pool.get('stock.production.lot')
        obj = self.browse(cr, uid, ids)[0]

        #if the production lot already blocked, raises an exception
        if obj.prodlot_id.blocked:
            raise osv.except_osv(_('Message !'), _('The production lot is blocked yet.'))
        elif obj.prodlot_id.in_alert:
            raise osv.except_osv(_('Message !'), _('The production lot is blocked yet.'))
        else:
            #gets all prodlots when this prodlot tooks part
            affected_prodlots = production_lot_obj.search_affected_prodlots(cr, uid, obj.prodlot_id.id, obj.firmness_grade == 'optimistic')

            affected_prodlots.append(obj.prodlot_id.id)

            blockade_id = self.pool.get('block.prodlot.cases').create(cr, uid, {
                                            'name': obj.case_name,
                                            'description': obj.case_description,
                                            'blocked_prodlots_ids': [(6, 0, affected_prodlots)],
                                            'parent_block_prodlot': obj.prodlot_id.id
                                            })

            production_lot_obj.write(cr, uid, affected_prodlots, {})

            view_id = self.pool.get('ir.ui.view').search(cr, uid, [('model', '=', 'block.prodlot.cases'), ('type', '=', 'tree')])[0]

            return {
                'name': _('Block Prodlot Case'),
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'block.prodlot.cases',
                'type': 'ir.actions.act_window',
                'domain': [('id', '=', blockade_id)],
                'nodestroy':True
            }

        return {'type': 'ir.actions.act_window_close'}

block_production_lot()
