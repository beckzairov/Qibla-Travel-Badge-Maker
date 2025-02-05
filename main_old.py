import time
import itertools
import sys
from PIL import Image, ImageDraw, ImageFont
from fpdf import FPDF
import os


class BadgeMaker:
    def __init__(self, template_men, template_women, backside_template, font_path, output_pdf, text_color):
        self.template_men = template_men
        self.template_women = template_women
        self.backside_template = backside_template
        self.font_path = font_path
        self.output_pdf = output_pdf
        self.text_color = text_color
        self.pages = []

    def get_scaled_font(self, draw, text, max_width, font_size_ratio, badge_height):
        """Find the largest font size that fits the text within the max_width."""
        font_size = int(badge_height * font_size_ratio)  # Font size as a ratio of badge height
        font = ImageFont.truetype(self.font_path, font_size)
        while draw.textbbox((0, 0), text, font=font)[2] > max_width:  # textbbox returns the text's width
            font_size -= 1
            font = ImageFont.truetype(self.font_path, font_size)
        return font

    def create_badge(self, name, group, template_path, badge_size):
        """Create a single badge with dynamically scaled text."""
        badge_width, badge_height = badge_size
        template = Image.open(template_path).convert("RGBA").resize(badge_size)
        draw = ImageDraw.Draw(template)

        # Split into surname and name
        surname, first_name = name.split(maxsplit=1)

        # Ratios for text alignment based on W=484px, H=724px template
        x_ratio = 45 / 484  # Horizontal padding ratio
        surname_y_ratio = 476 / 724  # Surname Y position ratio
        name_y_ratio = (476 + 40) / 724  # Name Y position ratio (adjusted for spacing)
        group_y_ratio = 0.92  # Group Y position ratio
        max_text_width_ratio = (484 - 2 * 45) / 484  # Max text width ratio

        # Convert ratios to pixel values for current badge size
        x_offset = int(badge_width * x_ratio)
        max_text_width = int(badge_width * max_text_width_ratio)
        surname_y = int(badge_height * surname_y_ratio)
        name_y = int(badge_height * name_y_ratio)
        group_y = int(badge_height * group_y_ratio)

        # Text size ratios (relative to badge height)
        surname_font_ratio = 0.06  # Surname font size
        name_font_ratio = 0.06     # Name font size
        group_font_ratio = 0.045   # Group font size

        # Get dynamically scaled fonts
        font_surname = self.get_scaled_font(draw, surname, max_text_width, surname_font_ratio, badge_height)
        font_first_name = self.get_scaled_font(draw, first_name, max_text_width, name_font_ratio, badge_height)
        font_group = self.get_scaled_font(draw, group, max_text_width, group_font_ratio, badge_height)

        # Draw surname
        surname_width, surname_height = draw.textbbox((0, 0), surname, font=font_surname)[2:]
        surname_x = x_offset + (max_text_width - surname_width) // 2
        draw.text((surname_x, surname_y), surname, font=font_surname, fill=self.text_color)

        # Draw first name
        first_name_width, first_name_height = draw.textbbox((0, 0), first_name, font=font_first_name)[2:]
        first_name_x = x_offset + (max_text_width - first_name_width) // 2
        draw.text((first_name_x, name_y), first_name, font=font_first_name, fill=self.text_color)

        # Draw group
        group_width, group_height = draw.textbbox((0, 0), group, font=font_group)[2:]
        group_x = x_offset + (max_text_width - group_width) // 2
        draw.text((group_x, group_y), group, font=font_group, fill=self.text_color)

        return template

    def write_text_on_backside(self, group, hotel_name, destination, badge_size):
        """Write text on the backside template."""
        badge_width, badge_height = badge_size
        template = Image.open(self.backside_template).convert("RGBA").resize(badge_size)
        draw = ImageDraw.Draw(template)

        # Group Text Position
        group_x_ratio = 45 / 482  # Horizontal position ratio for group name
        group_y_ratio = 0.92  # Vertical position ratio for group name
        max_text_width_ratio = 374 / 482  # Maximum text width ratio

        # Hotel Name Position
        hotel_x_ratio = 54 / 482  # Horizontal padding ratio for hotel name
        hotel_y_ratio = 98 / 722  # Vertical padding ratio for hotel name
        hotel_font_ratio = 0.065  # Slightly larger font size for hotel name

        # Destination Position
        destination_x_ratio = 54 / 482  # Horizontal padding ratio for destination
        destination_y_ratio = 8 / 722  # Vertical padding ratio for destination
        destination_font_ratio = 0.045  # Font size for destination text

        # Convert ratios to pixel positions
        group_x = int(badge_width * group_x_ratio)
        group_y = int(badge_height * group_y_ratio)
        max_text_width = int(badge_width * max_text_width_ratio)

        hotel_x = int(badge_width * hotel_x_ratio)
        hotel_y = int(badge_height * hotel_y_ratio)

        destination_x = int(badge_width * destination_x_ratio)
        destination_y = int(badge_height * destination_y_ratio)

        # Write Group Name
        font_group = self.get_scaled_font(draw, group, max_text_width, 0.045, badge_height)
        group_text_width, _ = draw.textbbox((0, 0), group, font=font_group)[2:]
        group_x_centered = group_x + (max_text_width - group_text_width) // 2
        draw.text((group_x_centered, group_y), group, font=font_group, fill=self.text_color)

        # Write Hotel Name
        font_hotel = self.get_scaled_font(draw, hotel_name, max_text_width, hotel_font_ratio, badge_height)
        hotel_text_width, _ = draw.textbbox((0, 0), hotel_name, font=font_hotel)[2:]
        hotel_x_centered = hotel_x + (max_text_width - hotel_text_width) // 2
        draw.text((hotel_x_centered, hotel_y), hotel_name, font=font_hotel, fill=(116, 87, 76))

        # Write Destination
        font_destination = self.get_scaled_font(draw, destination, max_text_width, destination_font_ratio, badge_height)
        destination_text_width, _ = draw.textbbox((0, 0), destination, font=font_destination)[2:]
        destination_x_centered = destination_x + (max_text_width - destination_text_width) // 2
        draw.text((destination_x_centered, destination_y), destination, font=font_destination, fill=self.text_color)

        return template

    def arrange_badges_on_page(self, badges, page_size, badge_size):
        """Arrange badges in a grid layout on an A4 page."""
        rows, cols = 3, 3
        x_padding_ratio, y_padding_ratio = 0.04706, 0.02376
        page = Image.new("RGBA", page_size, (255, 255, 255, 255))

        page_width, page_height = page_size
        x_padding = int(page_width * x_padding_ratio)
        y_padding = int(page_height * y_padding_ratio)

        badge_width, badge_height = badge_size
        for idx, badge in enumerate(badges):
            row = idx // cols
            col = idx % cols
            if row >= rows:
                break
            x = x_padding + col * badge_width
            y = y_padding + row * badge_height
            page.paste(badge, (x, y), badge)

        return page

    def create_pdf(self):
        """Save pages as a single PDF."""
        pdf = FPDF(unit="pt", format="A4")
        for idx, page in enumerate(self.pages):
            temp_path = f"temp_page_{idx}.png"
            page.save(temp_path, "PNG")
            pdf.add_page()
            pdf.image(temp_path, 0, 0, 595, 842)
            os.remove(temp_path)
        pdf.output(self.output_pdf)
        print(f"PDF saved as {self.output_pdf}")

    def process(self, names_with_gender, group, badge_size, page_size, hotel_name, destination):
        """Main processing logic with ETA and loading animation."""
        badges = []
        total_names = len(names_with_gender)
        total_batches = (total_names + 8) // 9  # Number of batches (9 badges per page)
        processed_batches = 0
        time_taken = 0
        spinner = itertools.cycle(["|", "/", "-", "\\"])  # Spinner animation

        for entry in names_with_gender:
            name = entry["name"]
            gender = entry["gender"]
            template_path = self.template_men if gender == "M" else self.template_women
            badge = self.create_badge(name, group, template_path, badge_size)
            badges.append(badge)

        for i in range(0, len(badges), 9):
            batch = badges[i:i + 9]
            start_time = time.time()  # Start timing this batch

            if len(batch) < 9:
                while len(batch) < 9:
                    blank_badge = Image.new("RGBA", badge_size, (255, 255, 255, 255))
                    batch.append(blank_badge)

            # Simulate processing with animation
            sys.stdout.write("\r")  # Return cursor to the start of the line
            sys.stdout.write(
                f"Processing batch {processed_batches + 1}/{total_batches} {next(spinner)}"
            )
            sys.stdout.flush()

            front_page = self.arrange_badges_on_page(batch, page_size, badge_size)
            self.pages.append(front_page)

            backside_batch = [self.write_text_on_backside(group, hotel_name, destination, badge_size) for _ in batch]
            back_page = self.arrange_badges_on_page(backside_batch, page_size, badge_size)
            self.pages.append(back_page)

            # Update processed batches and calculate ETA
            processed_batches += 1
            time_taken += time.time() - start_time
            avg_time_per_batch = time_taken / processed_batches
            remaining_batches = total_batches - processed_batches
            eta = avg_time_per_batch * remaining_batches

            # Display progress and ETA
            sys.stdout.write(
                f" | ETA: {int(eta)} seconds remaining..."
            )
            sys.stdout.flush()

        print("\nAll batches processed successfully!")  # New line after completion


# Input Data
names_with_gender = [
    {"name": "TUROPOV ABDULLOH", "gender": "M"},
]




group = "GROUP 149"
template_men = "M.png"
template_women = "F.png"
backside_template = "backside.png"
output_pdf = "149-Makkah-Rose.pdf"
font_path = "Unbounded-Bold.ttf"
text_color = (239, 219, 199)

# Badge and Page Sizes
a4_width, a4_height = 595, 842
page_size = (int(a4_width * 4), int(a4_height * 4))
badge_width = int((1 - 2 * 0.04706) * page_size[0] / 3)
badge_height = int((1 - 2 * 0.02376) * page_size[1] / 3)
badge_size = (badge_width, badge_height)

# Instantiate and Run
badge_maker = BadgeMaker(template_men, template_women, backside_template, font_path, output_pdf, text_color)
badge_maker.process(names_with_gender, group, badge_size, page_size, "Rose Garden", "Makkah")
badge_maker.create_pdf()
