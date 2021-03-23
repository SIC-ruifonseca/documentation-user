# -*- coding: utf-8 -*-
import os.path
import posixpath
import re

from docutils import nodes
from sphinx import addnodes, util, builders
from sphinx.locale import admonitionlabels
from sphinx.writers.html5 import HTML5Translator
#from urllib.request import url2pathname

# Translators inheritance chain:
# Docutils Base HTML translator: https://sourceforge.net/p/docutils/code/HEAD/tree/trunk/docutils/docutils/writers/_html_base.py
# └── Docutils Polyglot html5 translator: https://sourceforge.net/p/docutils/code/HEAD/tree/trunk/docutils/docutils/writers/html5_polyglot/__init__.py
#     └── Sphinx Translator: https://github.com/sphinx-doc/sphinx/blob/master/sphinx/writers/html5.py
#         └── Odoo Translator

ADMONITION_MAPPING = {
    # ???: 'alert-success',

    'note': 'alert-note',

    'hint': 'alert-info',

    'tip': 'alert-tip',

    'seealso': 'alert-go_to',

    'warning': 'alert-warning',
    'attention': 'alert-warning',
    'caution': 'alert-warning',
    'important': 'alert-warning',

    'danger': 'alert-danger',
    'error': 'alert-danger',

    'exercise': 'alert-exercise',
}


class BootstrapTranslator(HTML5Translator):
    # Docutils specifications
    head_prefix = 'head_prefix'
    head = 'head'
    stylesheet = 'stylesheet'
    body_prefix = 'body_prefix'
    body_pre_docinfo = 'body_pre_docinfo'
    docinfo = 'docinfo'
    body_suffix = 'body_suffix'
    subtitle = 'subtitle'
    header = 'header'
    footer = 'footer'
    html_prolog = 'html_prolog'
    html_head = 'html_head'
    html_title = 'html_title'
    html_subtitle = 'html_subtitle'


    def __init__(self, builder, *args, **kwds):
        super().__init__(builder, *args, **kwds)

        # Meta
        self.meta = ['', '']  # HTMLWriter strips out the first two items from Translator.meta
        self.add_meta('<meta http-equiv="X-UA-Compatible" content="IE=edge">')
        self.add_meta('<meta name="viewport" content="width=device-width, initial-scale=1">')

        # Body
        self.body = []
        self.fragment = self.body
        self.html_body = self.body
        # document title
        self.title = []
        self.start_document_title = 0
        self.first_title = False

        self.context = []
        self.section_level = 0

        # self.config = self.builder.config
        # self.highlightlang = self.highlightlang_base = self.builder.config.highlight_language

        self.first_param = 1
        self.param_separator = ','

    def encode(self, text):
        return str(text).translate({
            ord('&'): u'&amp;',
            ord('<'): u'&lt;',
            ord('"'): u'&quot;',
            ord('>'): u'&gt;',
            0xa0: u'&nbsp;'
        })

    # def add_meta(self, meta):
    #     self.meta.append('\n    ' + meta)

    # only "space characters" SPACE, CHARACTER TABULATION, LINE FEED,
    # FORM FEED and CARRIAGE RETURN should be collapsed, not al White_Space


    def unknown_visit(self, node):
        print("unknown node", node.__class__.__name__)
        self.body.append(u'[UNKNOWN NODE {}]'.format(node.__class__.__name__))
        raise nodes.SkipNode

    # VFE NOTE: seems that when we remove/comment this, we get 5 times the tiles in the global toc :D
    def visit_document(self, node):
        self.first_title = True
    def depart_document(self, node):
        pass

    # def visit_meta(self, node):
    #     if node.hasattr('lang'):
    #         node['xml:lang'] = node['lang']
    #     meta = self.starttag(node, 'meta', **node.non_default_attributes())
    #     self.add_meta(meta)
    # def depart_meta(self, node):
    #     pass

    # Breaks Accounting memento if commented
    def visit_section(self, node):
        # close "parent" or preceding section, unless this is the opening of
        # the first section
        if self.section_level:
            self.body.append(u'</section>')
        self.section_level += 1

        self.body.append(self.starttag(node, 'section'))
    def depart_section(self, node):
        self.section_level -= 1
        # close last section of document
        if not self.section_level:
            self.body.append(u'</section>')

    # # VFE FIXME do we need to keep this logic ?
    # # Seems that the only change is the use of a nav instead of a div.
    # def visit_topic(self, node):
    #     self.body.append(self.starttag(node, 'nav'))
    # def depart_topic(self, node):
    #     self.body.append(u'</nav>')

    # overwritten
    # Class mapping:
    # admonition [name] -> alert-[name]
    # Enforce presence of [name]-title as class on the <p> containing the title
    def visit_admonition(self, node, name=''):
        # type: (nodes.Node, unicode) -> None
        node_classes = ["alert"]
        if name:
            node_classes.append(ADMONITION_MAPPING[name])
        self.body.append(self.starttag(
            node, 'div', CLASS=" ".join(node_classes)))
        if name:
            node.insert(0, nodes.title(name, admonitionlabels[name]))

    # overwritten
    # Appends alert-title class to <p> if parent is an Admonition.
    def visit_title(self, node):
        # type: (nodes.Node) -> None
        if isinstance(node.parent, nodes.Admonition):
            self.body.append(self.starttag(node, 'p', CLASS='alert-title'))
        else:
            super().visit_title(node)

    def depart_title(self, node):
        if isinstance(node.parent, nodes.Admonition):
            self.body.append(u"</p>")
        else:
            super().depart_title(node)

    # overwritten
    # Ensure table class is present for tables
    def visit_table(self, node):
        # type: (nodes.Node) -> None
        self.generate_targets_for_table(node)

        self._table_row_index = 0

        classes = [cls.strip(u' \t\n')
                   for cls in self.settings.table_style.split(',')]
        classes.insert(0, "docutils")  # compat
        classes.insert(0, "table")  # compat

        if 'align' in node:
            classes.append('align-%s' % node['align'])
        tag = self.starttag(node, 'table', CLASS=' '.join(classes))
        self.body.append(tag)

    # def is_compact_paragraph(self, node):
    #     parent = node.parent
    #     if isinstance(parent, (nodes.document, nodes.compound,
    #                            addnodes.desc_content,
    #                            addnodes.versionmodified)):
    #         # Never compact paragraphs in document or compound.
    #         return False

    #     for key, value in node.attlist():
    #         # we can ignore a few specific classes, all other non-default
    #         # attributes require that a <p> node remains
    #         if key != 'classes' or value not in ([], ['first'], ['last'], ['first', 'last']):
    #             return False

    #     first = isinstance(node.parent[0], nodes.label)
    #     for child in parent.children[first:]:
    #         # only first paragraph can be compact
    #         if isinstance(child, nodes.Invisible):
    #             continue
    #         if child is node:
    #             break
    #         return False
    #     parent_length = len([
    #         1 for n in parent
    #         if not isinstance(n, (nodes.Invisible, nodes.label))
    #     ])
    #     return parent_length == 1

    # def visit_paragraph(self, node):
    #     if self.is_compact_paragraph(node):
    #         self.context.append(u'')
    #         return
    #     self.body.append(self.starttag(node, 'p'))
    #     self.context.append(u'</p>')
    # def depart_paragraph(self, node):
    #     self.body.append(self.context.pop())

    # def visit_problematic(self, node):
    #     if node.hasattr('refid'):
    #         self.body.append('<a href="#%s">' % node['refid'])
    #         self.context.append('</a>')
    #     else:
    #         self.context.append('')
    #     self.body.append(self.starttag(node, 'span', CLASS='problematic'))

    # def depart_problematic(self, node):
    #     self.body.append('</span>')
    #     self.body.append(self.context.pop())

    # def visit_bullet_list(self, node):
    #     self.body.append(self.starttag(node, 'ul'))
    # def depart_bullet_list(self, node):
    #     self.body.append(u'</ul>')
    # def visit_enumerated_list(self, node):
    #     self.body.append(self.starttag(node, 'ol'))
    # def depart_enumerated_list(self, node):
    #     self.body.append(u'</ol>')
    # def visit_list_item(self, node):
    #     self.body.append(self.starttag(node, 'li'))
    # def depart_list_item(self, node):
    #     self.body.append(u'</li>')
    # def visit_definition_list(self, node):
    #     self.body.append(self.starttag(node, 'dl'))
    # def depart_definition_list(self, node):
    #     self.body.append(u'</dl>')
    # def visit_definition_list_item(self, node):
    #     pass
    # def depart_definition_list_item(self, node):
    #     pass
    # def visit_term(self, node):
    #     self.body.append(self.starttag(node, 'dt'))
    # def depart_term(self, node):
    #     self.body.append(u'</dt>')
    # def visit_termsep(self, node):
    #     self.body.append(self.starttag(node, 'br'))
    #     raise nodes.SkipNode
    # def visit_definition(self, node):
    #     self.body.append(self.starttag(node, 'dd'))
    # def depart_definition(self, node):
    #     self.body.append(u'</dd>')

    # def visit_admonition(self, node, type=None):
    #     clss = {
    #         # ???: 'alert-success',

    #         'note': 'alert-info',
    #         'hint': 'alert-info',
    #         'tip': 'alert-info',
    #         'seealso': 'alert-go_to',

    #         'warning': 'alert-warning',
    #         'attention': 'alert-warning',
    #         'caution': 'alert-warning',
    #         'important': 'alert-warning',

    #         'danger': 'alert-danger',
    #         'error': 'alert-danger',

    #         'exercise': 'alert-exercise',
    #     }
    #     self.body.append(self.starttag(node, 'div', role='alert', CLASS='alert {}'.format(
    #         clss.get(type, '')
    #     )))
    #     if 'alert-dismissible' in node.get('classes', []):
    #         self.body.append(
    #             u'<button type="button" class="close" data-dismiss="alert" aria-label="Close">'
    #             u'<span aria-hidden="true">&times;</span>'
    #             u'</button>')
    #     if type:
    #         node.insert(0, nodes.title(type, admonitionlabels[type]))
    # def depart_admonition(self, node):
    #     self.body.append(u'</div>')

    # def visit_versionmodified(self, node):
    #     self.body.append(self.starttag(node, 'div', CLASS=node['type']))
    # def depart_versionmodified(self, node):
    #     self.body.append(u'</div>')

    # # the rubric should be a smaller heading than the current section, up to
    # # h6... maybe "h7" should be a ``p`` instead?
    # def visit_rubric(self, node):
    #     self.body.append(self.starttag(node, 'h{}'.format(min(self.section_level + 1, 6))))
    # def depart_rubric(self, node):
    #     self.body.append(u'</h{}>'.format(min(self.section_level + 1, 6)))

    # # one more div in the base class: keep it?
    # # def visit_block_quote(self, node):
    # #     self.body.append(self.starttag(node, 'blockquote'))
    # # def depart_block_quote(self, node):
    # #     self.body.append(u'</blockquote>')
    # def visit_attribution(self, node):
    #     self.body.append(self.starttag(node, 'footer'))
    # def depart_attribution(self, node):
    #     self.body.append(u'</footer>')

    # def visit_container(self, node):
    #     self.body.append(self.starttag(node, 'div'))
    # def depart_container(self, node):
    #     self.body.append(u'</div>')
    # def visit_compound(self, node):
    #     self.body.append(self.starttag(node, 'div'))
    # def depart_compound(self, node):
    #     self.body.append(u'</div>')

    # # overwritten, check if super can still be used
    # def visit_image(self, node):
    #     uri = node['uri']
    #     if uri in self.builder.images:
    #         uri = posixpath.join(self.builder.imgpath,
    #                              self.builder.images[uri])
    #     attrs = {'src': uri, 'class': 'img-fluid'}
    #     if 'alt' in node:
    #         attrs['alt'] = node['alt']
    #     if 'align' in node:
    #         if node['align'] == 'center':
    #             attrs['class'] += ' center-block'
    #         else:
    #             doc = None
    #             if node.source:
    #                 doc = node.source
    #                 if node.line:
    #                     doc += ':%d' % node.line
    #             self.builder.app.warn(
    #                 "Unsupported alignment value \"%s\"" % node['align'],
    #                 location=doc
    #             )
    #     elif 'align' in node.parent and node.parent['align'] == 'center':
    #         # figure > image
    #         attrs['class'] += ' center-block'

    #     # todo: explicit width/height/scale?
    #     self.body.append(self.starttag(node, 'img', **attrs))
    # def depart_image(self, node): pass
    # def visit_figure(self, node):
    #     self.body.append(self.starttag(node, 'div'))
    # def depart_figure(self, node):
    #     self.body.append(u'</div>')
    # # def visit_caption(self, node):
    # #     # first paragraph of figure content
    # #     self.body.append(self.starttag(node, 'h4'))
    # # def depart_caption(self, node):
    # #     self.body.append(u'</h4>')
    # def visit_legend(self, node): pass
    # def depart_legend(self, node): pass

    # def visit_line(self, node):
    #     self.body.append(self.starttag(node, 'div', CLASS='line'))
    #     # ensure the line still takes the room it needs
    #     if not len(node): self.body.append(u'<br />')
    # def depart_line(self, node):
    #     self.body.append(u'</div>')

    # def visit_line_block(self, node):
    #     self.body.append(self.starttag(node, 'div', CLASS='line-block'))
    # def depart_line_block(self, node):
    #     self.body.append(u'</div>')

    # # def visit_table(self, node):
    # #     self.body.append(self.starttag(node, 'table', CLASS='table'))
    # # def depart_table(self, node):
    # #     self.body.append(u'</table>')
    # def visit_tgroup(self, node): pass
    # def depart_tgroup(self, node): pass
    # def visit_colspec(self, node): raise nodes.SkipNode
    # def visit_thead(self, node):
    #     self.body.append(self.starttag(node, 'thead'))
    # def depart_thead(self, node):
    #     self.body.append(u'</thead>')
    # def visit_tbody(self, node):
    #     self.body.append(self.starttag(node, 'tbody'))
    # def depart_tbody(self, node):
    #     self.body.append(u'</tbody>')
    # def visit_row(self, node):
    #     self.body.append(self.starttag(node, 'tr'))
    # def depart_row(self, node):
    #     self.body.append(u'</tr>')
    # def visit_entry(self, node):
    #     if isinstance(node.parent.parent, nodes.thead):
    #         tagname = 'th'
    #     else:
    #         tagname = 'td'
    #     self.body.append(self.starttag(node, tagname))
    #     self.context.append(tagname)
    # def depart_entry(self, node):
    #     self.body.append(u'</{}>'.format(self.context.pop()))

    # # def visit_Text(self, node):
    # #     self.body.append(self.encode(node.astext()))
    # # def depart_Text(self, node):
    # #     pass
    # def visit_literal(self, node):
    #     self.body.append(self.starttag(node, 'code'))
    # def depart_literal(self, node):
    #     self.body.append(u'</code>')
    # visit_literal_emphasis = visit_literal
    # depart_literal_emphasis = depart_literal
    # def visit_emphasis(self, node):
    #     self.body.append(self.starttag(node, 'em'))
    # def depart_emphasis(self, node):
    #     self.body.append(u'</em>')
    # def visit_strong(self, node):
    #     self.body.append(self.starttag(node, 'strong'))
    # def depart_strong(self, node):
    #     self.body.append(u'</strong>')
    # visit_literal_strong = visit_strong
    # depart_literal_strong = depart_strong
    # def visit_inline(self, node):
    #     self.body.append(self.starttag(node, 'span'))
    # def depart_inline(self, node):
    #     self.body.append(u'</span>')

    # # def visit_download_reference(self, node):
    # #     # type: (nodes.Node) -> None
    # #     if node.hasattr('filename'):
    # #         self.body.append(
    # #             '<a class="reference download internal" href="%s" download="">' %
    # #             posixpath.join(self.builder.dlpath, node['filename']))
    # #         self.body.append(node.astext())
    # #         self.body.append('</a>')
    # #         raise nodes.SkipNode
    # #     else:
    # #         self.context.append('')
    # # def depart_download_reference(self, node):
    # #     # type: (nodes.Node) -> None
    # #     self.body.append(self.context.pop())
    # def visit_target(self, node): pass
    # def depart_target(self, node): pass
    # def visit_footnote(self, node):
    #     self.body.append(self.starttag(node, 'div', CLASS='footnote'))
    #     self.footnote_backrefs(node)
    # def depart_footnote(self, node):
    #     self.body.append(u'</div>')
    # def visit_footnote_reference(self, node):
    #     self.body.append(self.starttag(
    #         node, 'a', href='#' + node['refid'], CLASS="footnote-ref"))
    # def depart_footnote_reference(self, node):
    #     self.body.append(u'</a>')
    # def visit_label(self, node):
    #     self.body.append(self.starttag(node, 'span', CLASS='footnote-label'))
    #     self.body.append(u'%s[' % self.context.pop())
    # def depart_label(self, node):
    #     # Context added in footnote_backrefs.
    #     self.body.append(u']%s</span> %s' % (self.context.pop(), self.context.pop()))
    # def footnote_backrefs(self, node):
    #     # should store following data on context stack (in that order since
    #     # they'll be popped so LIFO)
    #     #
    #     # * outside (after) label
    #     # * after label text
    #     # * before label text
    #     backrefs = node['backrefs']
    #     if not backrefs:
    #         self.context.extend(['', '', ''])
    #     elif len(backrefs) == 1:
    #         self.context.extend([
    #             '',
    #             '</a>',
    #             '<a class="footnote-backref" href="#%s">' % backrefs[0]
    #         ])
    #     else:
    #         backlinks = (
    #             '<a class="footnote-backref" href="#%s">%s</a>' % (backref, i)
    #             for i, backref in enumerate(backrefs, start=1)
    #         )
    #         self.context.extend([
    #             '<em class="footnote-backrefs">(%s)</em> ' % ', '.join(backlinks),
    #             '',
    #             ''
    #         ])

    # def visit_desc(self, node):
    #     self.body.append(self.starttag(node, 'section', CLASS='code-' + node['objtype']))
    # def depart_desc(self, node):
    #     self.body.append(u'</section>')
    # def visit_desc_signature(self, node):
    #     self.body.append(self.starttag(node, 'h6'))
    #     self.body.append(u'<code>')
    # def depart_desc_signature(self, node):
    #     self.body.append(u'</code>')
    #     self.body.append(u'</h6>')
    # def visit_desc_addname(self, node): pass
    # def depart_desc_addname(self, node): pass
    # def visit_desc_type(self, node): pass
    # def depart_desc_type(self, node): pass
    # def visit_desc_returns(self, node):
    #     self.body.append(u' → ')
    # def depart_desc_returns(self, node):
    #     pass
    # def visit_desc_name(self, node): pass
    # def depart_desc_name(self, node): pass
    # def visit_desc_parameterlist(self, node):
    #     self.body.append(u'(')
    #     self.first_param = True
    #     self.optional_param_level = 0
    #     # How many required parameters are left.
    #     self.required_params_left = sum(isinstance(c, addnodes.desc_parameter) for c in node.children)
    #     self.param_separator = node.child_text_separator
    # def depart_desc_parameterlist(self, node):
    #     self.body.append(u')')
    # # If required parameters are still to come, then put the comma after
    # # the parameter.  Otherwise, put the comma before.  This ensures that
    # # signatures like the following render correctly (see issue #1001):
    # #
    # #     foo([a, ]b, c[, d])
    # #
    # def visit_desc_parameter(self, node):
    #     if self.first_param:
    #         self.first_param = 0
    #     elif not self.required_params_left:
    #         self.body.append(self.param_separator)
    #     if self.optional_param_level == 0:
    #         self.required_params_left -= 1
    #     if 'noemph' not in node: self.body.append(u'<em>')
    # def depart_desc_parameter(self, node):
    #     if 'noemph' not in node: self.body.append(u'</em>')
    #     if self.required_params_left:
    #         self.body.append(self.param_separator)
    # def visit_desc_optional(self, node):
    #     self.optional_param_level += 1
    #     self.body.append(u'[')
    # def depart_desc_optional(self, node):
    #     self.optional_param_level -= 1
    #     self.body.append(u']')
    # def visit_desc_annotation(self, node):
    #     self.body.append(self.starttag(node, 'em'))
    # def depart_desc_annotation(self, node):
    #     self.body.append(u'</em>')
    # def visit_desc_content(self, node): pass
    # def depart_desc_content(self, node): pass
    # def visit_field_list(self, node):
    #      self.body.append(self.starttag(node, 'div', CLASS='code-fields'))
    # def depart_field_list(self, node):
    #     self.body.append(u'</div>')
    # def visit_field(self, node):
    #     self.body.append(self.starttag(node, 'div', CLASS='code-field'))
    # def depart_field(self, node):
    #     self.body.append(u'</div>')
    # def visit_field_name(self, node):
    #     self.body.append(self.starttag(node, 'div', CLASS='code-field-name'))
    # def depart_field_name(self, node):
    #     self.body.append(u'</div>')
    # def visit_field_body(self, node):
    #     self.body.append(self.starttag(node, 'div', CLASS='code-field-body'))
    # def depart_field_body(self, node):
    #     self.body.append(u'</div>')

    # def visit_raw(self, node):
    #     if 'html' in node.get('format', '').split():
    #         t = 'span' if isinstance(node.parent, nodes.TextElement) else 'div'
    #         if node['classes']:
    #             self.body.append(self.starttag(node, t))
    #         self.body.append(node.astext())
    #         if node['classes']:
    #             self.body.append('</%s>' % t)
    #     # Keep non-HTML raw text out of output:
    #     raise nodes.SkipNode

    # # internal node
    # def visit_substitution_definition(self, node): raise nodes.SkipNode

    # # without set_translator, add_node doesn't work correctly, so the
    # # serialization of html_domain nodes needs to be embedded here
    # def visit_div(self, node):
    #     self.body.append(self.starttag(node, 'div'))
    # def depart_div(self, node):
    #     self.body.append(u'</div>\n')
    # def visit_address(self, node):
    #     self.body.append(self.starttag(node, 'address'))
    # def depart_address(self, node):
    #     self.body.append(u'</address>')
    # # TODO: inline elements
