# app.py - Simplified Clean Streamlit Application with Line-by-Line Merge
import streamlit as st
import difflib
from datetime import datetime
import uuid

# Page configuration
st.set_page_config(
    page_title="Mergely - Compare files and find differences",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize session state
if 'lhs_content' not in st.session_state:
    st.session_state.lhs_content = ""
if 'rhs_content' not in st.session_state:
    st.session_state.rhs_content = ""
if 'lhs_title' not in st.session_state:
    st.session_state.lhs_title = "Left Document"
if 'rhs_title' not in st.session_state:
    st.session_state.rhs_title = "Right Document"
if 'show_line_numbers' not in st.session_state:
    st.session_state.show_line_numbers = True
if 'ignore_whitespace' not in st.session_state:
    st.session_state.ignore_whitespace = False
if 'ignore_case' not in st.session_state:
    st.session_state.ignore_case = False
if 'auto_diff' not in st.session_state:
    st.session_state.auto_diff = False
if 'view_mode' not in st.session_state:
    st.session_state.view_mode = 'edit'
if 'diff_data' not in st.session_state:
    st.session_state.diff_data = None

# CSS Styling
def get_custom_css():
    return """
    <style>
    .main > div {
        padding-top: 2rem;
    }
    .diff-row {
        display: flex;
        gap: 10px;
        margin-bottom: 2px;
        align-items: stretch;
    }
    .diff-column-cell {
        flex: 1;
        border: 1px solid #ddd;
        background: white;
        font-family: 'Courier New', monospace;
        font-size: 13px;
        padding: 4px 8px;
        min-height: 24px;
        border-left: 3px solid transparent;
    }
    .diff-center-buttons {
        display: flex;
        flex-direction: column;
        gap: 2px;
        justify-content: center;
        min-width: 80px;
    }
    .line-number {
        display: inline-block;
        width: 45px;
        color: #999;
        text-align: right;
        padding-right: 12px;
        user-select: none;
    }
    .line-content {
        display: inline;
        white-space: pre;
    }
    .deleted-line {
        background-color: #ffe9e9;
        border-left-color: #ff7f7f;
    }
    .added-line {
        background-color: #e6f3ff;
        border-left-color: #4da6ff;
    }
    .changed-line {
        background-color: #fff8e6;
        border-left-color: #ffcc00;
    }
    .deleted-char {
        background-color: #ffb3b3;
        text-decoration: line-through;
        color: #cc0000;
    }
    .added-char {
        background-color: #99ccff;
        color: #0066cc;
        font-weight: bold;
    }
    .stats-container {
        display: flex;
        gap: 20px;
        padding: 12px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 8px;
        margin: 10px 0;
        color: white;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .stat-box {
        flex: 1;
        text-align: center;
        padding: 8px;
        background: rgba(255,255,255,0.1);
        border-radius: 6px;
        backdrop-filter: blur(10px);
    }
    .stat-number {
        font-size: 24px;
        font-weight: bold;
        display: block;
        margin-bottom: 3px;
    }
    .stat-label {
        font-size: 12px;
        opacity: 0.9;
    }
    .toolbar {
        background: #f8f9fa;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 20px;
        border: 1px solid #e0e0e0;
    }
    .column-header {
        padding: 10px;
        background: #f0f0f0;
        border-bottom: 2px solid #ddd;
        font-weight: bold;
        text-align: center;
        margin-bottom: 10px;
    }
    </style>
    """

# Diff computation functions
def normalize_text(text, ignore_ws=False, ignore_case=False):
    """Normalize text based on settings"""
    if ignore_case:
        text = text.lower()
    if ignore_ws:
        lines = text.split('\n')
        lines = [' '.join(line.split()) for line in lines]
        text = '\n'.join(lines)
    return text

def get_inline_diff(str1, str2):
    """Get character-level differences for inline highlighting"""
    s = difflib.SequenceMatcher(None, str1, str2)
    deleted = []
    added = []
    
    for tag, i1, i2, j1, j2 in s.get_opcodes():
        if tag == 'replace':
            deleted.append((i1, i2))
            added.append((j1, j2))
        elif tag == 'delete':
            deleted.append((i1, i2))
        elif tag == 'insert':
            added.append((j1, j2))
    
    return deleted, added

def highlight_inline_changes(text, ranges, char_class):
    """Apply inline highlighting to text"""
    if not ranges:
        return text
    
    result = []
    last_pos = 0
    
    for start, end in ranges:
        result.append(text[last_pos:start])
        result.append(f'<span class="{char_class}">{text[start:end]}</span>')
        last_pos = end
    
    result.append(text[last_pos:])
    return ''.join(result)

def generate_diff_structure(text1, text2):
    """Generate structured diff data for line-by-line manipulation"""
    text1_normalized = normalize_text(text1, st.session_state.ignore_whitespace, st.session_state.ignore_case)
    text2_normalized = normalize_text(text2, st.session_state.ignore_whitespace, st.session_state.ignore_case)
    
    lines1 = text1.split('\n')
    lines2 = text2.split('\n')
    
    lines1_normalized = text1_normalized.split('\n')
    lines2_normalized = text2_normalized.split('\n')
    
    differ = difflib.Differ()
    diff = list(differ.compare(lines1_normalized, lines2_normalized))
    
    diff_rows = []
    lhs_line_num = 0
    rhs_line_num = 0
    
    stats = {'deleted': 0, 'added': 0, 'changed': 0}
    
    i = 0
    while i < len(diff):
        line = diff[i]
        
        if line.startswith('  '):  # unchanged
            row = {
                'type': 'unchanged',
                'lhs_line_num': lhs_line_num + 1,
                'rhs_line_num': rhs_line_num + 1,
                'lhs_content': lines1[lhs_line_num] if lhs_line_num < len(lines1) else '',
                'rhs_content': lines2[rhs_line_num] if rhs_line_num < len(lines2) else '',
                'lhs_highlighted': line[2:],
                'rhs_highlighted': line[2:],
            }
            diff_rows.append(row)
            lhs_line_num += 1
            rhs_line_num += 1
            
        elif line.startswith('- '):  # deleted
            content = line[2:]
            lhs_original = lines1[lhs_line_num] if lhs_line_num < len(lines1) else ''
            
            # Check if next line is an addition (potential change)
            if i + 1 < len(diff) and diff[i + 1].startswith('+ '):
                next_content = diff[i + 1][2:]
                rhs_original = lines2[rhs_line_num] if rhs_line_num < len(lines2) else ''
                
                deleted_ranges, added_ranges = get_inline_diff(content, next_content)
                highlighted_deleted = highlight_inline_changes(content, deleted_ranges, 'deleted-char')
                highlighted_added = highlight_inline_changes(next_content, added_ranges, 'added-char')
                
                row = {
                    'type': 'changed',
                    'lhs_line_num': lhs_line_num + 1,
                    'rhs_line_num': rhs_line_num + 1,
                    'lhs_content': lhs_original,
                    'rhs_content': rhs_original,
                    'lhs_highlighted': highlighted_deleted,
                    'rhs_highlighted': highlighted_added,
                }
                diff_rows.append(row)
                stats['changed'] += 1
                lhs_line_num += 1
                rhs_line_num += 1
                i += 1
            else:
                # Pure deletion
                row = {
                    'type': 'deleted',
                    'lhs_line_num': lhs_line_num + 1,
                    'rhs_line_num': None,
                    'lhs_content': lhs_original,
                    'rhs_content': '',
                    'lhs_highlighted': content,
                    'rhs_highlighted': '',
                }
                diff_rows.append(row)
                stats['deleted'] += 1
                lhs_line_num += 1
                
        elif line.startswith('+ '):  # added
            content = line[2:]
            rhs_original = lines2[rhs_line_num] if rhs_line_num < len(lines2) else ''
            
            row = {
                'type': 'added',
                'lhs_line_num': None,
                'rhs_line_num': rhs_line_num + 1,
                'lhs_content': '',
                'rhs_content': rhs_original,
                'lhs_highlighted': '',
                'rhs_highlighted': content,
            }
            diff_rows.append(row)
            stats['added'] += 1
            rhs_line_num += 1
            
        elif line.startswith('? '):
            pass
            
        i += 1
    
    return diff_rows, stats

def move_line_to_right(row_index):
    """Move a line from left to right"""
    if st.session_state.diff_data:
        row = st.session_state.diff_data[row_index]
        content = row['lhs_content']
        
        # Update right content
        lines = st.session_state.rhs_content.split('\n')
        if row['rhs_line_num'] is not None:
            lines[row['rhs_line_num'] - 1] = content
        else:
            # Insert at appropriate position
            lines.insert(row_index, content)
        
        st.session_state.rhs_content = '\n'.join(lines)
        st.session_state.view_mode = 'compare'
        st.rerun()

def move_line_to_left(row_index):
    """Move a line from right to left"""
    if st.session_state.diff_data:
        row = st.session_state.diff_data[row_index]
        content = row['rhs_content']
        
        # Update left content
        lines = st.session_state.lhs_content.split('\n')
        if row['lhs_line_num'] is not None:
            lines[row['lhs_line_num'] - 1] = content
        else:
            # Insert at appropriate position
            lines.insert(row_index, content)
        
        st.session_state.lhs_content = '\n'.join(lines)
        st.session_state.view_mode = 'compare'
        st.rerun()

# Apply custom CSS
st.markdown(get_custom_css(), unsafe_allow_html=True)

# Header
st.title("📄 Text Comparison Tool")

# Toolbar with options in a single row
st.markdown('<div class="toolbar">', unsafe_allow_html=True)
toolbar_col1, toolbar_col2, toolbar_col3, toolbar_col4 = st.columns(4)

with toolbar_col1:
    st.session_state.show_line_numbers = st.checkbox("🔢 Line Numbers", value=st.session_state.show_line_numbers)

with toolbar_col2:
    st.session_state.ignore_whitespace = st.checkbox("⚪ Ignore Whitespace", value=st.session_state.ignore_whitespace)
    
with toolbar_col3:
    st.session_state.ignore_case = st.checkbox("🔤 Ignore Case", value=st.session_state.ignore_case)

with toolbar_col4:
    st.session_state.auto_diff = st.checkbox("🔄 Auto Diff", value=st.session_state.auto_diff)

st.markdown('</div>', unsafe_allow_html=True)

# Action buttons row
btn_col1, btn_col2, btn_col3, btn_col4 = st.columns(4)

with btn_col1:
    if st.button("🔍 Compare", use_container_width=True, type="primary"):
        st.session_state.view_mode = 'compare'
        st.rerun()

with btn_col2:
    if st.button("📝 Edit Mode", use_container_width=True):
        st.session_state.view_mode = 'edit'
        st.rerun()

with btn_col3:
    if st.button("🔄 Swap", use_container_width=True):
        st.session_state.lhs_content, st.session_state.rhs_content = st.session_state.rhs_content, st.session_state.lhs_content
        st.session_state.lhs_title, st.session_state.rhs_title = st.session_state.rhs_title, st.session_state.lhs_title
        st.rerun()

with btn_col4:
    if st.button("🗑️ Clear", use_container_width=True):
        st.session_state.lhs_content = ""
        st.session_state.rhs_content = ""
        st.session_state.view_mode = 'edit'
        st.rerun()

# Auto diff logic
if st.session_state.auto_diff and (st.session_state.lhs_content or st.session_state.rhs_content):
    st.session_state.view_mode = 'compare'

# Main content area
if st.session_state.view_mode == 'compare' and (st.session_state.lhs_content or st.session_state.rhs_content):
    # Generate diff structure
    diff_rows, stats = generate_diff_structure(
        st.session_state.lhs_content,
        st.session_state.rhs_content
    )
    st.session_state.diff_data = diff_rows
    
    # Display statistics
    st.markdown(f"""
    <div class="stats-container">
        <div class="stat-box">
            <span class="stat-number">{stats['deleted']}</span>
            <span class="stat-label">🗑️ Deleted</span>
        </div>
        <div class="stat-box">
            <span class="stat-number">{stats['added']}</span>
            <span class="stat-label">➕ Added</span>
        </div>
        <div class="stat-box">
            <span class="stat-number">{stats['changed']}</span>
            <span class="stat-label">✏️ Changed</span>
        </div>
        <div class="stat-box">
            <span class="stat-number">{stats['deleted'] + stats['added'] + stats['changed']}</span>
            <span class="stat-label">📊 Total</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Column headers
    col1, col2, col3 = st.columns([5, 1, 5])
    with col1:
        st.markdown(f'<div class="column-header">⬅️ {st.session_state.lhs_title}</div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="column-header">Actions</div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="column-header">➡️ {st.session_state.rhs_title}</div>', unsafe_allow_html=True)
    
    # Display each diff row with merge buttons
    for idx, row in enumerate(diff_rows):
        col1, col2, col3 = st.columns([5, 1, 5])
        
        with col1:
            # Left side content
            line_num = f'<span class="line-number">{row["lhs_line_num"]}</span>' if st.session_state.show_line_numbers and row["lhs_line_num"] else '<span class="line-number"> </span>'
            
            css_class = ""
            if row['type'] == 'deleted':
                css_class = "deleted-line"
            elif row['type'] == 'changed':
                css_class = "changed-line"
            
            content = row['lhs_highlighted'] if row['lhs_highlighted'] else " "
            st.markdown(f'<div class="diff-column-cell {css_class}">{line_num}<span class="line-content">{content}</span></div>', unsafe_allow_html=True)
        
        with col2:
            # Merge buttons
            if row['type'] in ['deleted', 'changed'] and row['lhs_content']:
                if st.button("→", key=f"right_{idx}", help="Move to right", use_container_width=True):
                    move_line_to_right(idx)
            
            if row['type'] in ['added', 'changed'] and row['rhs_content']:
                if st.button("←", key=f"left_{idx}", help="Move to left", use_container_width=True):
                    move_line_to_left(idx)
        
        with col3:
            # Right side content
            line_num = f'<span class="line-number">{row["rhs_line_num"]}</span>' if st.session_state.show_line_numbers and row["rhs_line_num"] else '<span class="line-number"> </span>'
            
            css_class = ""
            if row['type'] == 'added':
                css_class = "added-line"
            elif row['type'] == 'changed':
                css_class = "changed-line"
            
            content = row['rhs_highlighted'] if row['rhs_highlighted'] else " "
            st.markdown(f'<div class="diff-column-cell {css_class}">{line_num}<span class="line-content">{content}</span></div>', unsafe_allow_html=True)
    
    # Download button
    st.markdown("<br>", unsafe_allow_html=True)
    if st.session_state.lhs_content and st.session_state.rhs_content:
        lines1 = st.session_state.lhs_content.split('\n')
        lines2 = st.session_state.rhs_content.split('\n')
        diff = difflib.unified_diff(
            lines1,
            lines2,
            fromfile=st.session_state.lhs_title,
            tofile=st.session_state.rhs_title,
            lineterm=''
        )
        diff_content = '\n'.join(diff)
        
        st.download_button(
            label="💾 Download Diff File",
            data=diff_content,
            file_name=f"diff_{datetime.now().strftime('%Y%m%d_%H%M%S')}.diff",
            mime="text/plain",
            use_container_width=False
        )

else:
    # Show text editors
    col1, col2 = st.columns(2)
    
    with col1:
        st.session_state.lhs_title = st.text_input(
            "Left Title",
            value=st.session_state.lhs_title,
            placeholder="Left Document Title",
            key="lhs_title_input"
        )
        
        st.session_state.lhs_content = st.text_area(
            "Left Content",
            value=st.session_state.lhs_content,
            height=400,
            placeholder="Paste or type your left text here...",
            key="lhs_textarea"
        )
    
    with col2:
        st.session_state.rhs_title = st.text_input(
            "Right Title",
            value=st.session_state.rhs_title,
            placeholder="Right Document Title",
            key="rhs_title_input"
        )
        
        st.session_state.rhs_content = st.text_area(
            "Right Content",
            value=st.session_state.rhs_content,
            height=400,
            placeholder="Paste or type your right text here...",
            key="rhs_textarea"
        )

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 20px;">
    <p style="font-size: 14px;">✨ Built with Streamlit | Compare text and merge line-by-line</p>
    <p style="font-size: 12px;">Use ← and → buttons to move individual lines between documents</p>
</div>
""", unsafe_allow_html=True)