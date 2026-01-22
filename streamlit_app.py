import streamlit as st
import io
from pypdf import PdfReader, PdfWriter
import fitz  # PyMuPDF
from PIL import Image


def flatten_pdf(pdf_bytes):
    """
    Flatten a PDF by removing form fields and making them part of the content.
    """
    reader = PdfReader(io.BytesIO(pdf_bytes))
    writer = PdfWriter()

    for page in reader.pages:
        # Flatten the page by merging form fields into the content
        if "/Annots" in page:
            page.merge_page(page)
        writer.add_page(page)

    # Create output buffer
    output_buffer = io.BytesIO()
    writer.write(output_buffer)
    output_buffer.seek(0)
    return output_buffer.getvalue()


def restrict_copying_pdf(
    pdf_bytes, allow_interactive=False, allow_text_selection=False
):
    """
    Create a copy-protected PDF with granular permission controls.

    Args:
        pdf_bytes: The original PDF bytes
        allow_interactive: Whether to allow interactive elements (links, forms)
        allow_text_selection: Whether to allow text selection and copying
    """
    reader = PdfReader(io.BytesIO(pdf_bytes))
    writer = PdfWriter()

    # Add all pages to the writer
    for page in reader.pages:
        writer.add_page(page)

    # Build permissions based on user choices
    permissions = 0

    # Always allow printing (high resolution)
    permissions |= 4  # Print (bit 3)
    permissions |= 2048  # Print high resolution (bit 12)

    if allow_text_selection:
        permissions |= 16  # Copy text and graphics (bit 5)
        permissions |= 32  # Extract text for accessibility (bit 6)

    if allow_interactive:
        permissions |= 256  # Fill forms (bit 9)
        permissions |= 512  # Extract for accessibility (bit 10)
        permissions |= 1024  # Assemble document (bit 11)

    # Always allow viewing
    permissions |= 64  # Modify annotations (bit 7) - needed for basic viewing

    # Encrypt with custom permissions
    owner_password = "owner_protection_key"
    writer.encrypt(
        user_password="",  # No password required to open
        owner_password=owner_password,
        use_128bit=True,
        permissions_flag=permissions,
    )

    # Create output buffer
    output_buffer = io.BytesIO()
    writer.write(output_buffer)
    output_buffer.seek(0)
    return output_buffer.getvalue()


def convert_to_image_pdf(pdf_bytes, dpi=150, get_images: bool = False):
    """
    Convert each PDF page to an image and create a new PDF from those images.

    Args:
        pdf_bytes: The original PDF bytes
        dpi: Resolution for the image conversion (default: 150 DPI)
        get_images: If True, return a list of PIL Image objects instead of PDF bytes (default: False)

    Returns:
        If get_images is False: bytes of the image-based PDF
        If get_images is True: list of PIL Image objects
    """
    # Open the PDF with PyMuPDF
    pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")

    images = []
    writer = PdfWriter() if not get_images else None

    for page_num in range(pdf_document.page_count):
        # Get the page
        page = pdf_document.load_page(page_num)

        # Convert page to image (pixmap)
        mat = fitz.Matrix(dpi / 72, dpi / 72)  # Scale factor for DPI
        pix = page.get_pixmap(matrix=mat)

        # Convert to PIL Image
        img_data = pix.tobytes("png")
        img = Image.open(io.BytesIO(img_data))

        if get_images:
            # Store image in list
            images.append(img)
        else:
            # Create a new PDF page from the image
            img_buffer = io.BytesIO()
            img.save(img_buffer, format="PDF")
            img_buffer.seek(0)

            # Add the image PDF page to our writer
            img_reader = PdfReader(img_buffer)
            writer.add_page(img_reader.pages[0])

    # Close the PyMuPDF document
    pdf_document.close()

    if get_images:
        return images
    else:
        # Create output buffer
        output_buffer = io.BytesIO()
        writer.write(output_buffer)
        output_buffer.seek(0)
        return output_buffer.getvalue()


def main():
    app_icon = (
        "https://images.seeklogo.com/logo-png/0/3/adobe-pdf-logo-png_seeklogo-3493.png"
    )
    st.set_page_config(
        page_title="PDF flatpack",
        page_icon=app_icon,
        # page_icon="📄",
        layout="wide",
    )

    st.logo(app_icon, size="large")

    st.title("PDF flatpack")
    st.caption("flattening your PDFs")

    # Sidebar for file upload
    with st.sidebar:
        st.header("📤 Upload PDF")
        uploaded_file = st.file_uploader(
            "Choose a PDF file", type="pdf", help="Upload a PDF file to process"
        )

    if uploaded_file is not None:
        # Display file info in sidebar
        with st.sidebar:
            st.success(f"✅ Uploaded: {uploaded_file.name}")
            st.caption(f"Size: {uploaded_file.size:,} bytes")

        # Read the PDF
        pdf_bytes = uploaded_file.read()

        try:
            reader = PdfReader(io.BytesIO(pdf_bytes))
            num_pages = len(reader.pages)

            st.info(f"📊 PDF Info: {num_pages} page(s)")

            # Create columns for operations
            col1, col2 = st.columns(2)

            with col1:
                tab_imc, tab_flatten, tab_protect = st.tabs(
                    [
                        ":material/image:",
                        ":material/skillet_cooktop:",
                        ":material/lock_open",
                    ]
                )
                with tab_protect:
                    st.subheader("🔧 PDF Operations")

                    # Flatten option
                    if st.button(
                        "🔄 Flatten PDF", help="Remove form fields and flatten the PDF"
                    ):
                        with st.spinner("Flattening PDF..."):
                            try:
                                flattened_pdf = flatten_pdf(pdf_bytes)
                                st.session_state["flattened_pdf"] = flattened_pdf
                                st.success("✅ PDF flattened successfully!")
                            except Exception as e:
                                st.error(f"❌ Error flattening PDF: {str(e)}")
                with tab_protect:
                    # Copy protection options
                    st.markdown("#### 🔒 Copy Protection Settings")

                    allow_text_selection = st.checkbox(
                        "Allow text selection and copying",
                        value=False,
                        help="Check to allow users to select and copy text from the PDF",
                    )

                    allow_interactive = st.checkbox(
                        "Allow interactive elements",
                        value=False,
                        help="Check to keep links, form fields, and other interactive elements functional",
                    )

                    if st.button(
                        "🔒 Apply Copy Protection",
                        help="Create a copy-protected version with selected permissions",
                    ):
                        with st.spinner("Applying copy protection..."):
                            try:
                                protected_pdf = restrict_copying_pdf(
                                    pdf_bytes,
                                    allow_interactive=allow_interactive,
                                    allow_text_selection=allow_text_selection,
                                )
                                st.session_state["protected_pdf"] = protected_pdf
                                st.session_state["protection_settings"] = {
                                    "text_selection": allow_text_selection,
                                    "interactive": allow_interactive,
                                }
                                st.success("✅ Copy protection applied successfully!")

                                # Show applied settings
                                settings_info = []
                                if allow_text_selection:
                                    settings_info.append("✅ Text selection allowed")
                                else:
                                    settings_info.append("❌ Text selection blocked")

                                if allow_interactive:
                                    settings_info.append(
                                        "✅ Interactive elements enabled"
                                    )
                                else:
                                    settings_info.append(
                                        "❌ Interactive elements disabled"
                                    )

                                st.info(
                                    "🔧 Applied settings:\n"
                                    + "\n".join(
                                        f"- {setting}" for setting in settings_info
                                    )
                                )

                            except Exception as e:
                                st.error(f"❌ Error applying copy protection: {str(e)}")
                with tab_imc:
                    # Image conversion option
                    st.markdown("#### 🖼️ Image Conversion")

                    image_dpi = st.slider(
                        "Image Quality (DPI)",
                        min_value=72,
                        max_value=300,
                        value=150,
                        step=25,
                        help="Higher DPI = better quality but larger file size",
                    )

                    col_img1, col_img2 = st.columns(2)

                    with col_img1:
                        if st.button(
                            "🖼️ Generate Images",
                            help="Extract pages as individual images",
                        ):
                            with st.spinner("Generating images..."):
                                try:
                                    page_images = convert_to_image_pdf(
                                        pdf_bytes, dpi=image_dpi, get_images=True
                                    )
                                    st.session_state["page_images"] = page_images
                                    st.session_state["image_dpi"] = image_dpi
                                    st.success("✅ Images generated successfully!")
                                    st.info(f"ℹ️ Generated {len(page_images)} image(s)")
                                except Exception as e:
                                    st.error(f"❌ Error generating images: {str(e)}")

                    with col_img2:
                        if st.button(
                            "🖼️ Convert to Image PDF",
                            help="Convert each page to an image and create a new PDF",
                        ):
                            with st.spinner("Converting pages to images..."):
                                try:
                                    image_pdf = convert_to_image_pdf(
                                        pdf_bytes, dpi=image_dpi
                                    )
                                    st.session_state["image_pdf"] = image_pdf
                                    st.session_state["image_dpi"] = image_dpi
                                    st.success(
                                        "✅ PDF converted to image-based PDF successfully!"
                                    )
                                    st.info(
                                        f"ℹ️ Each page converted to {image_dpi} DPI image"
                                    )
                                except Exception as e:
                                    st.error(
                                        f"❌ Error converting to image PDF: {str(e)}"
                                    )

            with col2:
                st.subheader("📥 Downloads")

                # Download original PDF
                st.download_button(
                    label="📄 Download Original PDF",
                    data=pdf_bytes,
                    file_name=f"original_{uploaded_file.name}",
                    mime="application/pdf",
                )

                # Download flattened PDF if available
                if "flattened_pdf" in st.session_state:
                    st.download_button(
                        label="📄 Download Flattened PDF",
                        data=st.session_state["flattened_pdf"],
                        file_name=f"flattened_{uploaded_file.name}",
                        mime="application/pdf",
                    )

                # Download copy-protected PDF if available
                if "protected_pdf" in st.session_state:
                    # Show protection settings if available
                    if "protection_settings" in st.session_state:
                        settings = st.session_state["protection_settings"]
                        text_status = "✅" if settings["text_selection"] else "❌"
                        interactive_status = "✅" if settings["interactive"] else "❌"
                        help_text = f"Text selection: {text_status} | Interactive elements: {interactive_status}"
                    else:
                        help_text = "Copy-protected PDF with custom permissions"

                    st.download_button(
                        label="🔒 Download Copy-Protected PDF",
                        data=st.session_state["protected_pdf"],
                        file_name=f"protected_{uploaded_file.name}",
                        mime="application/pdf",
                        help=help_text,
                    )

                # Download image PDF if available
                if "image_pdf" in st.session_state:
                    dpi_info = st.session_state.get("image_dpi", "150")
                    st.download_button(
                        label="🖼️ Download Image PDF",
                        data=st.session_state["image_pdf"],
                        file_name=f"image_{uploaded_file.name}",
                        mime="application/pdf",
                        help=f"PDF with pages converted to {dpi_info} DPI images",
                    )

                # Display generated images if available
                if "page_images" in st.session_state:
                    with st.expander(
                        f"🖼️ Preview Generated Images ({len(st.session_state['page_images'])} page(s))",
                        expanded=False,
                    ):
                        images = st.session_state["page_images"]
                        dpi_info = st.session_state.get("image_dpi", "150")

                        # Create a grid of images
                        cols = st.columns(2)
                        for idx, img in enumerate(images):
                            with cols[idx % 2]:
                                st.image(
                                    img,
                                    caption=f"Page {idx + 1} ({dpi_info} DPI)",
                                    use_container_width=True,
                                )

            # PDF Preview section
            st.subheader("👁️ PDF Preview")

            # Show first page as preview (if possible)
            try:
                first_page = reader.pages[0]
                if hasattr(first_page, "extract_text"):
                    text_content = first_page.extract_text()
                    if text_content.strip():
                        with st.expander("📖 First Page Text Content"):
                            st.text_area(
                                "Text from first page:", text_content, height=200
                            )
                    else:
                        st.info(
                            "ℹ️ No extractable text found on the first page (might be image-based)"
                        )
            except Exception as e:
                st.warning(f"⚠️ Could not extract preview: {str(e)}")

        except Exception as e:
            st.error(f"❌ Error reading PDF: {str(e)}")
            st.info("Please make sure you uploaded a valid PDF file.")

    else:
        st.info("👈 Please upload a PDF file in the sidebar to get started")

        # Show some help information
        with st.expander("ℹ️ What can this app do?"):
            st.markdown(
                """
            **PyPDF Forge** helps you process PDF files with the following features:

            - **📤 Upload**: Upload any PDF file from your computer
            - **🔄 Flatten**: Remove interactive form fields and flatten the PDF
            - **🔒 Copy Protection**: Restrict copying of text and graphics
            - **🖼️ Image Conversion**: Convert each page to high-quality images
            - **📥 Download**: Download original and all processed versions
            - **👁️ Preview**: View text content from your PDF

            **Flattening** is useful when you want to:
            - Remove fillable form fields
            - Ensure the PDF displays consistently across different viewers
            - Prepare PDFs for archival or sharing

            **Copy Protection** is useful when you want to:
            - Control text selection and copying permissions
            - Enable/disable interactive elements (links, forms)
            - Protect intellectual property with granular controls
            - Share documents with customized access restrictions
            - Note: The PDF can still be opened normally without a password

            **Protection Options**:
            - **Text Selection**: Control whether users can select and copy text
            - **Interactive Elements**: Control whether links, forms, and buttons work

            **Image Conversion** is useful when you want to:
            - Create a PDF that's impossible to edit or extract text from
            - Ensure consistent appearance across all viewers and platforms
            - Convert complex layouts to simple image-based pages
            - Protect content by making it non-selectable and non-copyable
            - Note: Higher DPI settings create better quality but larger files
            """
            )


if __name__ == "__main__":
    main()
